"""EKARUSwiki admin: overview, messages from the wiki, wiki sign-in list, editable home
content and server accounts. The observation schedule has its own admin section
(schedule/admin.py) linked from here.

Changes to the wiki are committed to its GitHub repository (see github.py); GitHub Pages
publishes them within a minute or two.
"""
import json
from datetime import date

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from . import github, mail, wiki_users
from .db import get_db, now
from .security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

SITE_PATH = "docs/data/site.json"
EXTRA_ROWS = 3


def new_messages():
    return get_db().execute("SELECT COUNT(*) FROM messages WHERE status = 'new'").fetchone()[0]


@bp.app_context_processor
def inject_counts():
    if getattr(g, "user", None) is not None and g.user["is_admin"]:
        return {"new_message_count": new_messages()}
    return {}


# ---------------------------------------------------------------- overview
@bp.route("/")
@admin_required
def overview():
    db = get_db()
    today = date.today().isoformat()
    counts = {
        "new_messages": new_messages(),
        "open_messages": db.execute("SELECT COUNT(*) FROM messages WHERE status != 'done'").fetchone()[0],
        "to_review": db.execute("SELECT COUNT(*) FROM proposals WHERE status = 'submitted'").fetchone()[0],
        "open_nights": db.execute("SELECT COUNT(*) FROM nights WHERE status = 'open' AND date >= ?", (today,)).fetchone()[0],
        "booked_nights": db.execute("SELECT COUNT(*) FROM nights WHERE status = 'booked' AND date >= ?", (today,)).fetchone()[0],
        "accounts": db.execute("SELECT COUNT(*) FROM users WHERE password_hash NOT LIKE '!%'").fetchone()[0],
        "team": db.execute("SELECT COUNT(*) FROM team").fetchone()[0],
    }
    return render_template("admin/overview.html", c=counts, github_ok=github.configured())


# ---------------------------------------------------------------- server accounts
@bp.route("/accounts")
@admin_required
def accounts():
    rows = get_db().execute(
        "SELECT u.*, (SELECT COUNT(*) FROM proposals p WHERE p.user_id = u.id) AS n_prop"
        " FROM users u ORDER BY u.created_at DESC").fetchall()
    return render_template("admin/accounts.html", users=rows)


# ---------------------------------------------------------------- messages
@bp.route("/messages")
@admin_required
def messages():
    show = request.args.get("show", "open")
    sql = "SELECT * FROM messages"
    if show == "open":
        sql += " WHERE status != 'done'"
    sql += " ORDER BY id DESC"
    return render_template("admin/messages.html", messages=get_db().execute(sql).fetchall(), show=show)


@bp.route("/messages/<int:mid>", methods=["GET", "POST"])
@admin_required
def message(mid):
    db = get_db()
    m = db.execute("SELECT * FROM messages WHERE id = ?", (mid,)).fetchone()
    if m is None:
        abort(404)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "approve" and m["kind"] == "access":
            added, sync_note = add_team_member(m["email"], m["name"])
            db.execute("UPDATE messages SET status = 'done' WHERE id = ?", (mid,))
            db.commit()
            mail.send(m["email"], "You now have access to the EKARUS wiki", "access_approved",
                      name=m["name"], wiki_url=current_app.config["WIKI_URL"])
            flash(("Added to the team" if added else "Already on the team") +
                  f"; {m['email']} has been told by e-mail. {sync_note}", "ok")
            return redirect(url_for("admin.messages"))
        if action in ("done", "new"):
            db.execute("UPDATE messages SET status = ? WHERE id = ?", (action, mid))
            db.commit()
            flash("Marked as done." if action == "done" else "Marked as unread.", "ok")
            return redirect(url_for("admin.messages"))
    if m["status"] == "new":
        db.execute("UPDATE messages SET status = 'read' WHERE id = ?", (mid,))
        db.commit()
    return render_template("admin/message.html", m=m)


# ---------------------------------------------------------------- team members
def _sync_wiki_list(email, add):
    """Keep the wiki's own sign-in list (users.js, used when the server is off) in step.
    Returns a short note for the admin; never raises."""
    if not github.configured():
        return ("The wiki's offline list wasn't updated (no GITHUB_TOKEN); "
                "team sign-in works anyway while the server is on.")
    try:
        text, sha = github.read(wiki_users.PATH)
        header, entries = wiki_users.parse(text)
        h = wiki_users.email_hash(email)
        hashes = [x for x, _ in entries]
        if add and h not in hashes:
            entries.append((h, ""))
        elif not add and h in hashes:
            entries = [(x, n) for x, n in entries if x != h]
        else:
            return ""
        github.write(wiki_users.PATH, wiki_users.serialize(header, entries), sha,
                     f"{'Add' if add else 'Remove'} a team member (by {g.user['name']} via admin page)")
        return "The wiki's offline list was updated too."
    except github.GitHubError as e:
        return f"The wiki's offline list couldn't be updated: {e}"


def add_team_member(email, name=""):
    email = email.strip().lower()
    db = get_db()
    if db.execute("SELECT 1 FROM team WHERE email = ?", (email,)).fetchone():
        return False, ""
    db.execute("INSERT INTO team (email, name, added_at) VALUES (?, ?, ?)", (email, name.strip()[:120], now()))
    db.commit()
    return True, _sync_wiki_list(email, True)


@bp.route("/team", methods=["GET", "POST"])
@admin_required
def team_members():
    db = get_db()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if "@" not in email:
            flash("Enter an e-mail address.", "error")
        elif request.form.get("action") == "add":
            added, note = add_team_member(email, request.form.get("name", ""))
            flash((f"{email} added to the team. " if added else f"{email} is already on the team. ") + note, "ok")
        elif request.form.get("action") == "remove":
            cur = db.execute("DELETE FROM team WHERE email = ?", (email,))
            db.commit()
            if cur.rowcount:
                flash(f"{email} removed from the team. " + _sync_wiki_list(email, False), "ok")
            else:
                flash(f"{email} isn't in the team list.", "error")
        return redirect(url_for("admin.team_members"))
    rows = db.execute(
        "SELECT t.*, u.created_at AS first_signin FROM team t LEFT JOIN users u ON u.email = t.email"
        " ORDER BY t.name COLLATE NOCASE, t.email").fetchall()
    return render_template("admin/team.html", members=rows, admins=mail.admin_addresses(),
                           github_ok=github.configured())


# ---------------------------------------------------------------- home page content
@bp.route("/wiki-content", methods=["GET", "POST"])
@admin_required
def wiki_content():
    try:
        text, sha = github.read(SITE_PATH)
        site = json.loads(text)
    except github.GitHubError as e:
        return render_template("admin/wiki_content.html", site=None, error=str(e), rows=[])
    except ValueError:
        site, sha = {"banner": "", "highlights": []}, None

    if request.method == "POST":
        dates, titles = request.form.getlist("h_date"), request.form.getlist("h_title")
        texts, dones = request.form.getlist("h_text"), request.form.getlist("h_done")
        highlights = []
        for i in range(len(titles)):
            row = {"date": dates[i].strip()[:60], "title": titles[i].strip()[:200],
                   "text": texts[i].strip()[:1500], "done": dones[i] == "yes"}
            if row["title"] or row["text"]:
                highlights.append(row)
        new = {"banner": request.form.get("banner", "").strip()[:200], "highlights": highlights}
        try:
            github.write(SITE_PATH, json.dumps(new, ensure_ascii=False, indent=2) + "\n", sha,
                         f"Update home page content (by {g.user['name']} via admin page)")
            flash("Saved. The wiki shows the change within a minute or two.", "ok")
        except github.GitHubError as e:
            flash(str(e), "error")
        return redirect(url_for("admin.wiki_content"))

    rows = site.get("highlights", []) + [{"date": "", "title": "", "text": "", "done": False}] * EXTRA_ROWS
    return render_template("admin/wiki_content.html", site=site, rows=rows, error=None)
