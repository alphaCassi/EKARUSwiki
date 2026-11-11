"""Observation schedule, admin side: review proposals, cancel allocations, open/close nights."""
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import mail
from ..db import get_db, now
from ..security import admin_required
from .views import add_event, load_proposal

bp = Blueprint("schedule_admin", __name__, url_prefix="/admin/schedule")

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
    return render_template("schedule/admin/dashboard.html", proposals=proposals, status=status, counts=counts)


def _open_nights_for(pid, nights):
    """Nights the admin can allocate: the proposal's requested nights that are still open,
    plus any other upcoming open night (useful when the requested ones are gone)."""
    requested_open = [n for n in nights if n["status"] == "open"]
    others = get_db().execute(
        "SELECT * FROM nights WHERE status = 'open' AND date >= ? AND id NOT IN"
        " (SELECT night_id FROM proposal_nights WHERE proposal_id = ?) ORDER BY date",
        (date.today().isoformat(), pid)).fetchall()
    return requested_open, others


def _allocate(p, picked, message, reconsidered=False):
    db = get_db()
    pid = p["id"]
    booked = 0
    for nid in picked:
        cur = db.execute("UPDATE nights SET status = 'booked', proposal_id = ? WHERE id = ? AND status = 'open'",
                         (pid, nid))
        booked += cur.rowcount
        db.execute("INSERT OR IGNORE INTO proposal_nights (proposal_id, night_id) VALUES (?, ?)", (pid, nid))
    if not booked:
        db.rollback()
        return 0
    db.execute("UPDATE proposals SET status = 'accepted', admin_message = ?, updated_at = ? WHERE id = ?",
               (message, now(), pid))
    add_event(pid, "accepted after reconsideration" if reconsidered else "accepted", message)
    db.commit()
    p2, _, nights, _ = load_proposal(pid)
    allocated = [n for n in nights if n["proposal_id"] == pid]
    mail.send(p2["pi_email"], f"{p2['code']} accepted", "accepted", p=p2, allocated=allocated,
              message=message, link=url_for("schedule.view_proposal", pid=pid))
    return booked


@bp.route("/proposals/<int:pid>", methods=["GET", "POST"])
@admin_required
def review(pid):
    p, targets, nights, events = load_proposal(pid)
    db = get_db()
    if request.method == "POST":
        decision = request.form.get("decision")
        message = request.form.get("message", "").strip()
        picked = {int(x) for x in request.form.getlist("allocate") if x.isdigit()}

        if decision in ("accept", "reconsider"):
            allowed = p["status"] == "submitted" if decision == "accept" else p["status"] in ("rejected", "withdrawn")
            if not allowed:
                flash("This proposal's status changed in the meantime; the page has been refreshed.", "error")
            elif not picked:
                flash("Tick at least one open night to allocate.", "error")
            else:
                n = _allocate(p, picked, message, reconsidered=(decision == "reconsider"))
                if n:
                    flash(f"{p['code']} accepted; {n} night(s) booked and the PI notified.", "ok")
                    return redirect(url_for("schedule_admin.dashboard"))
                flash("Those nights were booked by someone else in the meantime. Choose other open nights.", "error")

        elif decision == "reject":
            if p["status"] != "submitted":
                flash("This proposal's status changed in the meantime; the page has been refreshed.", "error")
            else:
                message = message or "The requested nights could not be allocated this time."
                db.execute("UPDATE proposals SET status = 'rejected', admin_message = ?, updated_at = ? WHERE id = ?",
                           (message, now(), pid))
                add_event(pid, "rejected", message)
                db.commit()
                mail.send(p["pi_email"], f"{p['code']} not accepted", "rejected", p=p, message=message,
                          link=url_for("schedule.view_proposal", pid=pid))
                flash(f"{p['code']} rejected and the PI notified. You can still accept it later from its page.", "ok")
                return redirect(url_for("schedule_admin.dashboard"))
        else:
            flash("Choose accept or reject.", "error")
        p, targets, nights, events = load_proposal(pid)

    requested_open, others = _open_nights_for(pid, nights)
    return render_template("schedule/admin/review.html", p=p, targets=targets, nights=nights, events=events,
                           requested_open=requested_open, other_open=others)


@bp.route("/proposals/<int:pid>/cancel", methods=["POST"])
@admin_required
def cancel(pid):
    """Undo an acceptance (e.g. telescope unavailable): frees the nights and tells the PI."""
    p, _, _, _ = load_proposal(pid)
    message = request.form.get("message", "").strip() or "The allocated nights had to be cancelled."
    if p["status"] != "accepted":
        flash("Only accepted proposals can be cancelled.", "error")
        return redirect(url_for("schedule_admin.review", pid=pid))
    db = get_db()
    db.execute("UPDATE nights SET status = 'open', proposal_id = NULL WHERE proposal_id = ?", (pid,))
    db.execute("UPDATE proposals SET status = 'rejected', admin_message = ?, updated_at = ? WHERE id = ?",
               (message, now(), pid))
    add_event(pid, "cancelled", message)
    db.commit()
    mail.send(p["pi_email"], f"{p['code']} allocation cancelled", "cancelled", p=p, message=message,
              link=url_for("schedule.view_proposal", pid=pid))
    flash(f"{p['code']} cancelled; its nights are open again and the PI was notified.", "ok")
    return redirect(url_for("schedule_admin.dashboard"))


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
                return redirect(url_for("schedule_admin.nights"))
            if end < start or (end - start).days > MAX_RANGE_DAYS:
                flash("The end date must be after the start, within one year.", "error")
                return redirect(url_for("schedule_admin.nights"))
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
                pending = db.execute(
                    "SELECT p.code FROM proposal_nights pn JOIN proposals p ON p.id = pn.proposal_id"
                    " WHERE pn.night_id = ? AND p.status = 'submitted'", (nid,)).fetchall()
                if pending:
                    flash(f"{', '.join(r['code'] for r in pending)} waiting for review requested this night: "
                          "decide on them first, or close the night instead of removing it.", "error")
                else:
                    # requests from rejected or withdrawn proposals don't block the removal
                    db.execute("DELETE FROM proposal_nights WHERE night_id = ?", (nid,))
                    db.execute("DELETE FROM nights WHERE id = ?", (nid,))
                    db.commit()
                    flash(f"{night['date']} removed from the calendar.", "ok")
            else:
                db.execute("UPDATE nights SET status = ? WHERE id = ?",
                           ("closed" if action == "close" else "open", nid))
                db.commit()
                flash(f"{night['date']} {'closed' if action == 'close' else 'reopened'}.", "ok")
        return redirect(url_for("schedule_admin.nights", show=request.args.get("show", "upcoming")))

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
    return render_template("schedule/admin/nights.html", nights=db.execute(sql, args).fetchall(), show=show)
