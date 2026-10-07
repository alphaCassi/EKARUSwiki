"""Admin area: review proposals, open/close nights, see users."""
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import mail
from .db import get_db, now
from .main import add_event, load_proposal
from .security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

MAX_RANGE_DAYS = 370


@bp.route("/")
@admin_required
def dashboard():
    db = get_db()
    status = request.args.get("status", "submitted")
    if status not in ("submitted", "accepted", "rejected", "withdrawn", "all"):
        status = "submitted"
    sql = ("SELECT p.*, u.name AS pi_name, u.institute AS pi_institute,"
           " (SELECT COUNT(*) FROM proposal_nights pn WHERE pn.proposal_id = p.id) AS n_req,"
           " (SELECT MIN(n.date) FROM nights n JOIN proposal_nights pn ON pn.night_id = n.id"
           "  WHERE pn.proposal_id = p.id) AS first_night"
           " FROM proposals p JOIN users u ON u.id = p.user_id")
    args = ()
    if status != "all":
        sql += " WHERE p.status = ?"
        args = (status,)
    sql += " ORDER BY first_night IS NULL, first_night, p.id"
    proposals = db.execute(sql, args).fetchall()
    counts = dict(db.execute("SELECT status, COUNT(*) FROM proposals GROUP BY status").fetchall())
    return render_template("admin/dashboard.html", proposals=proposals, status=status, counts=counts)


@bp.route("/proposals/<int:pid>", methods=["GET", "POST"])
@admin_required
def review(pid):
    p, targets, nights, events = load_proposal(pid)
    db = get_db()
    if request.method == "POST":
        decision = request.form.get("decision")
        message = request.form.get("message", "").strip()
        if p["status"] != "submitted":
            flash("This proposal has already been decided.", "error")
            return redirect(url_for("admin.review", pid=pid))

        if decision == "accept":
            requested = {n["id"] for n in nights if n["status"] == "open"}
            picked = {int(x) for x in request.form.getlist("allocate") if x.isdigit()} & requested
            if not picked:
                flash("Select at least one available night to allocate.", "error")
            else:
                for nid in picked:
                    db.execute("UPDATE nights SET status = 'booked', proposal_id = ? WHERE id = ? AND status = 'open'",
                               (pid, nid))
                db.execute("UPDATE proposals SET status = 'accepted', admin_message = ?, updated_at = ? WHERE id = ?",
                           (message, now(), pid))
                add_event(pid, "accepted", message)
                db.commit()
                p, targets, nights, events = load_proposal(pid)
                allocated = [n for n in nights if n["proposal_id"] == pid]
                mail.send(p["pi_email"], f"{p['code']} accepted", "accepted", p=p, allocated=allocated,
                          message=message, link=url_for("main.view_proposal", pid=pid))
                flash(f"{p['code']} accepted; {len(allocated)} night(s) booked and the PI notified.", "ok")
                return redirect(url_for("admin.dashboard"))

        elif decision == "reject":
            if not message:
                flash("Add a short reason for the rejection; the PI will receive it.", "error")
            else:
                db.execute("UPDATE proposals SET status = 'rejected', admin_message = ?, updated_at = ? WHERE id = ?",
                           (message, now(), pid))
                add_event(pid, "rejected", message)
                db.commit()
                mail.send(p["pi_email"], f"{p['code']} not accepted", "rejected", p=p, message=message,
                          link=url_for("main.view_proposal", pid=pid))
                flash(f"{p['code']} rejected and the PI notified.", "ok")
                return redirect(url_for("admin.dashboard"))
        else:
            flash("Choose accept or reject.", "error")

    return render_template("admin/review.html", p=p, targets=targets, nights=nights, events=events)


@bp.route("/proposals/<int:pid>/cancel", methods=["POST"])
@admin_required
def cancel(pid):
    """Undo an acceptance (e.g. telescope unavailable): frees the nights and tells the PI."""
    p, _, _, _ = load_proposal(pid)
    message = request.form.get("message", "").strip()
    if p["status"] != "accepted" or not message:
        flash("Only accepted proposals can be cancelled, and a reason is required.", "error")
        return redirect(url_for("admin.review", pid=pid))
    db = get_db()
    db.execute("UPDATE nights SET status = 'open', proposal_id = NULL WHERE proposal_id = ?", (pid,))
    db.execute("UPDATE proposals SET status = 'rejected', admin_message = ?, updated_at = ? WHERE id = ?",
               (message, now(), pid))
    add_event(pid, "cancelled", message)
    db.commit()
    mail.send(p["pi_email"], f"{p['code']} allocation cancelled", "cancelled", p=p, message=message,
              link=url_for("main.view_proposal", pid=pid))
    flash(f"{p['code']} cancelled; its nights are open again and the PI was notified.", "ok")
    return redirect(url_for("admin.dashboard"))


@bp.route("/nights", methods=["GET", "POST"])
@admin_required
def nights():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            try:
                start = date.fromisoformat(request.form.get("start", ""))
                end = date.fromisoformat(request.form.get("end", "") or request.form.get("start", ""))
            except ValueError:
                flash("Enter valid dates.", "error")
                return redirect(url_for("admin.nights"))
            if end < start or (end - start).days > MAX_RANGE_DAYS:
                flash("The end date must be after the start, within one year.", "error")
                return redirect(url_for("admin.nights"))
            note = request.form.get("note", "").strip()
            added = 0
            d = start
            while d <= end:
                cur = db.execute("INSERT OR IGNORE INTO nights (date, note) VALUES (?, ?)", (d.isoformat(), note))
                added += cur.rowcount
                d += timedelta(days=1)
            db.commit()
            flash(f"{added} night(s) opened for proposals."
                  + (" Dates already in the calendar were left unchanged." if added <= (end - start).days else ""),
                  "ok")
        elif action in ("close", "open", "remove"):
            nid = request.form.get("night_id", "")
            night = db.execute("SELECT * FROM nights WHERE id = ?", (nid,)).fetchone()
            if night is None:
                flash("Night not found.", "error")
            elif night["status"] == "booked":
                flash("This night is booked. Cancel the proposal's allocation first.", "error")
            elif action == "remove":
                used = db.execute("SELECT 1 FROM proposal_nights WHERE night_id = ?", (nid,)).fetchone()
                if used:
                    flash("Proposals have requested this night; close it instead of removing it.", "error")
                else:
                    db.execute("DELETE FROM nights WHERE id = ?", (nid,))
                    db.commit()
                    flash(f"{night['date']} removed from the calendar.", "ok")
            else:
                db.execute("UPDATE nights SET status = ? WHERE id = ?",
                           ("closed" if action == "close" else "open", nid))
                db.commit()
                flash(f"{night['date']} {'closed' if action == 'close' else 'reopened'}.", "ok")
        return redirect(url_for("admin.nights", show=request.args.get("show", "upcoming")))

    show = request.args.get("show", "upcoming")
    sql = ("SELECT n.*, p.code AS booked_code,"
           " (SELECT COUNT(*) FROM proposal_nights pn JOIN proposals q ON q.id = pn.proposal_id"
           "  WHERE pn.night_id = n.id AND q.status = 'submitted') AS pending"
           " FROM nights n LEFT JOIN proposals p ON p.id = n.proposal_id")
    args = ()
    if show != "all":
        sql += " WHERE n.date >= ?"
        args = (date.today().isoformat(),)
    sql += " ORDER BY n.date"
    return render_template("admin/nights.html", nights=db.execute(sql, args).fetchall(), show=show)


@bp.route("/users")
@admin_required
def users():
    rows = get_db().execute(
        "SELECT u.*, (SELECT COUNT(*) FROM proposals p WHERE p.user_id = u.id) AS n_prop"
        " FROM users u ORDER BY u.created_at DESC").fetchall()
    return render_template("admin/users.html", users=rows)
