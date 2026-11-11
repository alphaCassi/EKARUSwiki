"""Observation schedule module: night calendar and proposals for observers."""
import calendar as pycal
from datetime import date

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for

from .. import mail, wiki_pages
from ..db import get_db, now
from ..security import login_required

bp = Blueprint("schedule", __name__)   # the observation schedule is the server's main site

MODES = [
    "VIS imaging",
    "NIR imaging",
    "Wavefront sensing / AO tests",
    "Engineering / calibration",
    "Other (describe in notes)",
]
MAX_TARGETS = 30


def month_grid(year, month, nights_by_date):
    """Weeks (Mon-Sun) of (date, night-or-None) for one month; None for padding days."""
    weeks = []
    for week in pycal.Calendar(firstweekday=0).monthdatescalendar(year, month):
        weeks.append([(d, nights_by_date.get(d.isoformat())) if d.month == month else (None, None)
                      for d in week])
    return weeks


def add_event(proposal_id, action, message=""):
    get_db().execute(
        "INSERT INTO events (proposal_id, created_at, actor_id, action, message) VALUES (?, ?, ?, ?, ?)",
        (proposal_id, now(), g.user["id"] if g.user else None, action, message))


def load_proposal(pid):
    db = get_db()
    p = db.execute(
        "SELECT p.*, u.name AS pi_name, u.email AS pi_email, u.institute AS pi_institute"
        " FROM proposals p JOIN users u ON u.id = p.user_id WHERE p.id = ?", (pid,)).fetchone()
    if p is None:
        abort(404)
    from ..security import is_admin_session
    if not (is_admin_session() or p["user_id"] == g.user["id"]):
        abort(403)
    targets = db.execute("SELECT * FROM proposal_targets WHERE proposal_id = ? ORDER BY id", (pid,)).fetchall()
    nights = db.execute(
        "SELECT n.* FROM nights n JOIN proposal_nights pn ON pn.night_id = n.id"
        " WHERE pn.proposal_id = ? ORDER BY n.date", (pid,)).fetchall()
    events = db.execute(
        "SELECT e.*, u.name AS actor FROM events e LEFT JOIN users u ON u.id = e.actor_id"
        " WHERE e.proposal_id = ? ORDER BY e.id", (pid,)).fetchall()
    return p, targets, nights, events


def month_data(year, month):
    """Nights of one month for the calendar (shown only to signed-in users)."""
    from ..security import is_admin_session
    first = date(year, month, 1)
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    prev = date(year - (month == 1), (month - 2) % 12 + 1, 1)
    db = get_db()
    rows = db.execute(
        "SELECT n.*, p.user_id AS owner, p.code AS code FROM nights n"
        " LEFT JOIN proposals p ON p.id = n.proposal_id WHERE n.date >= ? AND n.date < ? ORDER BY n.date",
        (first.isoformat(), nxt.isoformat())).fetchall()
    admin = is_admin_session()
    nights = []
    for r in rows:
        mine = r["status"] == "booked" and r["owner"] == g.user["id"]
        nights.append({"id": r["id"], "date": r["date"], "status": r["status"], "note": r["note"],
                       "mine": mine, "code": r["code"] if (mine or admin) else ""})
    return {"year": year, "month": month, "title": first.strftime("%B %Y"), "today": date.today().isoformat(),
            "prev": {"y": prev.year, "m": prev.month}, "next": {"y": nxt.year, "m": nxt.month},
            "nights": nights}


def _month_args():
    today = date.today()
    try:
        y, m = int(request.args.get("y", today.year)), int(request.args.get("m", today.month))
        date(y, m, 1)
        return y, m
    except ValueError:
        return today.year, today.month


@bp.route("/")
@login_required
def calendar():
    y, m = _month_args()
    db = get_db()
    today = date.today().isoformat()
    upcoming = db.execute(
        "SELECT * FROM nights WHERE status = 'open' AND date >= ? ORDER BY date LIMIT 8", (today,)).fetchall()
    upcoming_open = db.execute(
        "SELECT COUNT(*) FROM nights WHERE status = 'open' AND date >= ?", (today,)).fetchone()[0]
    return render_template("schedule/calendar.html", initial=month_data(y, m),
                           upcoming=upcoming, upcoming_open=upcoming_open)


@bp.route("/calendar.json")
@login_required
def calendar_json():
    y, m = _month_args()
    resp = jsonify(month_data(y, m))
    resp.headers["Cache-Control"] = "private, max-age=30"
    return resp


@bp.route("/dashboard")
@bp.route("/proposals")
@login_required
def dashboard():
    """The observer's dashboard: their proposals with status, and their allocated nights."""
    db = get_db()
    rows = db.execute(
        "SELECT p.*, (SELECT COUNT(*) FROM proposal_nights pn WHERE pn.proposal_id = p.id) AS n_req,"
        " (SELECT COUNT(*) FROM nights n WHERE n.proposal_id = p.id) AS n_alloc"
        " FROM proposals p WHERE p.user_id = ? ORDER BY p.id DESC", (g.user["id"],)).fetchall()
    upcoming = db.execute(
        "SELECT n.date, p.code, p.title, p.id AS pid FROM nights n JOIN proposals p ON p.id = n.proposal_id"
        " WHERE p.user_id = ? AND n.date >= ? ORDER BY n.date", (g.user["id"], date.today().isoformat())).fetchall()
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ("submitted", "accepted", "rejected", "withdrawn")}
    return render_template("schedule/dashboard.html", proposals=rows, upcoming=upcoming, counts=counts)


@bp.route("/info/<page>")
@login_required
def info(page):
    """Telescope, bench and team pages, taken from the published wiki (one source of content)."""
    if page not in wiki_pages.PAGES:
        abort(404)
    html, error = wiki_pages.get(page)
    return render_template("schedule/info.html", page=page, title=wiki_pages.PAGES[page][1],
                           content=html, error=error)


@bp.route("/proposals/new", methods=["GET", "POST"])
@login_required
def new_proposal():
    db = get_db()
    open_nights = db.execute(
        "SELECT * FROM nights WHERE status = 'open' AND date >= ? ORDER BY date",
        (date.today().isoformat(),)).fetchall()
    open_ids = {n["id"] for n in open_nights}

    form = {k: request.form.get(k, "").strip() for k in
            ("title", "summary", "science_case", "mode", "observers", "constraints", "min_nights", "notes")}
    targets, chosen = [], set()
    if request.method == "GET" and request.args.get("night", "").isdigit():
        chosen = {int(request.args["night"])} & open_ids

    if request.method == "POST":
        names, ras = request.form.getlist("t_name"), request.form.getlist("t_ra")
        decs, mags = request.form.getlist("t_dec"), request.form.getlist("t_mag")
        for i, name in enumerate(names[:MAX_TARGETS]):
            row = {"name": name.strip(), "ra": _get(ras, i), "dec": _get(decs, i), "mag": _get(mags, i)}
            if any(row.values()):
                targets.append(row)
        chosen = {int(x) for x in request.form.getlist("nights") if x.isdigit()}

        errors = []
        if not form["title"]:
            errors.append("Give the proposal a title.")
        if not form["science_case"]:
            errors.append("Describe the science or technical case.")
        if form["mode"] not in MODES:
            errors.append("Choose an observing mode.")
        if any(not t["name"] for t in targets):
            errors.append("Every target row needs a name.")
        if not chosen:
            errors.append("Select at least one night.")
        if chosen - open_ids:
            errors.append("Some selected nights are no longer available. Check the selection again.")
            chosen &= open_ids
        try:
            min_n = max(1, int(form["min_nights"] or 1))
        except ValueError:
            min_n = 1
        if chosen and min_n > len(chosen):
            errors.append("The minimum number of useful nights can't exceed the nights you selected.")

        if not errors:
            year = date.today().year
            count = db.execute("SELECT COUNT(*) FROM proposals WHERE code LIKE ?", (f"EK-{year}-%",)).fetchone()[0]
            code = f"EK-{year}-{count + 1:03d}"
            ts = now()
            cur = db.execute(
                "INSERT INTO proposals (code, user_id, title, summary, science_case, mode, observers,"
                " constraints, min_nights, notes, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (code, g.user["id"], form["title"], form["summary"], form["science_case"], form["mode"],
                 form["observers"], form["constraints"], min_n, form["notes"], ts, ts))
            pid = cur.lastrowid
            db.executemany("INSERT INTO proposal_targets (proposal_id, name, ra, dec, mag) VALUES (?, ?, ?, ?, ?)",
                           [(pid, t["name"], t["ra"], t["dec"], t["mag"]) for t in targets])
            db.executemany("INSERT INTO proposal_nights (proposal_id, night_id) VALUES (?, ?)",
                           [(pid, nid) for nid in sorted(chosen)])
            add_event(pid, "submitted")
            db.commit()

            p, tg, ng, _ = load_proposal(pid)
            mail.send(g.user["email"], f"{code} received", "submitted_user", p=p, nights=ng)
            mail.send(mail.admin_addresses(), f"New proposal {code}: {p['title']}", "submitted_admin",
                      p=p, nights=ng, targets=tg, link=url_for("schedule_admin.review", pid=pid))
            flash(f"Proposal {code} submitted. You'll get an e-mail when it's reviewed.", "ok")
            return redirect(url_for("schedule.view_proposal", pid=pid))
        for e in errors:
            flash(e, "error")

    by_month = {}
    for n in open_nights:
        by_month.setdefault(n["date"][:7], []).append(n)
    return render_template("schedule/proposals/new.html", form=form, modes=MODES, by_month=by_month,
                           targets=targets or [{"name": "", "ra": "", "dec": "", "mag": ""}],
                           chosen=chosen, max_targets=MAX_TARGETS)


def _get(values, i):
    return values[i].strip() if i < len(values) else ""


@bp.route("/proposals/<int:pid>")
@login_required
def view_proposal(pid):
    p, targets, nights, events = load_proposal(pid)
    return render_template("schedule/proposals/view.html", p=p, targets=targets, nights=nights, events=events)


@bp.route("/proposals/<int:pid>/withdraw", methods=["POST"])
@login_required
def withdraw(pid):
    p, _, nights, _ = load_proposal(pid)
    if p["user_id"] != g.user["id"] or p["status"] != "submitted":
        flash("Only proposals waiting for review can be withdrawn. Contact the admin otherwise.", "error")
        return redirect(url_for("schedule.view_proposal", pid=pid))
    db = get_db()
    db.execute("UPDATE proposals SET status = 'withdrawn', updated_at = ? WHERE id = ?", (now(), pid))
    add_event(pid, "withdrawn")
    db.commit()
    mail.send(mail.admin_addresses(), f"{p['code']} withdrawn", "withdrawn_admin", p=p,
              link=url_for("schedule_admin.review", pid=pid))
    flash(f"{p['code']} withdrawn.", "ok")
    return redirect(url_for("schedule.dashboard"))
