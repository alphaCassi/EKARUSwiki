"""Admin pages for the wiki: messages from the wiki, wiki sign-in list, editable home content.

Changes to the wiki are committed to its GitHub repository (see github.py); GitHub Pages
publishes them within a minute or two.
"""
import json

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from . import github, mail, wiki_users
from .db import get_db
from .security import admin_required

bp = Blueprint("wiki_admin", __name__, url_prefix="/admin")

SITE_PATH = "docs/data/site.json"
EXTRA_ROWS = 3


def new_messages():
    return get_db().execute("SELECT COUNT(*) FROM messages WHERE status = 'new'").fetchone()[0]


@bp.app_context_processor
def inject_counts():
    if getattr(g, "user", None) is not None and g.user["is_admin"]:
        return {"new_message_count": new_messages()}
    return {}


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
            try:
                initials = "".join(w[0] for w in m["name"].split()[:3]).upper()
                added = _add_wiki_user(m["email"], initials)
            except github.GitHubError as e:
                flash(str(e), "error")
                return redirect(url_for("wiki_admin.message", mid=mid))
            db.execute("UPDATE messages SET status = 'done' WHERE id = ?", (mid,))
            db.commit()
            mail.send(m["email"], "You can now sign in to the EKARUS wiki", "access_approved",
                      name=m["name"], wiki_url=current_app.config["WIKI_URL"])
            flash(("Registered on the wiki" if added else "Already registered") +
                  f"; {m['email']} has been told by e-mail.", "ok")
            return redirect(url_for("wiki_admin.messages"))
        if action in ("done", "new"):
            db.execute("UPDATE messages SET status = ? WHERE id = ?", (action, mid))
            db.commit()
            flash("Marked as done." if action == "done" else "Marked as unread.", "ok")
            return redirect(url_for("wiki_admin.messages"))
    if m["status"] == "new":
        db.execute("UPDATE messages SET status = 'read' WHERE id = ?", (mid,))
        db.commit()
    return render_template("admin/message.html", m=m)


# ---------------------------------------------------------------- wiki sign-in list
def _add_wiki_user(email, note=""):
    text, sha = github.read(wiki_users.PATH)
    header, entries = wiki_users.parse(text)
    h = wiki_users.email_hash(email)
    if h in [x for x, _ in entries]:
        return False
    entries.append((h, note.replace("@", "").replace("\n", " ")[:40]))  # never store the address itself
    github.write(wiki_users.PATH, wiki_users.serialize(header, entries), sha,
                 f"Register a wiki user (by {g.user['name']} via admin page)")
    return True


@bp.route("/wiki-users", methods=["GET", "POST"])
@admin_required
def wiki_user_list():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        action = request.form.get("action")
        if "@" not in email:
            flash("Enter an e-mail address.", "error")
            return redirect(url_for("wiki_admin.wiki_user_list"))
        try:
            if action == "add":
                added = _add_wiki_user(email, request.form.get("note", "").strip())
                flash(f"{email} registered on the wiki." if added else f"{email} was already registered.", "ok")
            elif action == "remove":
                text, sha = github.read(wiki_users.PATH)
                header, entries = wiki_users.parse(text)
                h = wiki_users.email_hash(email)
                if h not in [x for x, _ in entries]:
                    flash(f"{email} isn't registered.", "error")
                else:
                    github.write(wiki_users.PATH,
                                 wiki_users.serialize(header, [(x, n) for x, n in entries if x != h]),
                                 sha, f"Remove a wiki user (by {g.user['name']} via admin page)")
                    flash(f"{email} removed from the wiki.", "ok")
        except github.GitHubError as e:
            flash(str(e), "error")
        return redirect(url_for("wiki_admin.wiki_user_list"))

    entries, error = [], None
    try:
        _, entries = wiki_users.parse(github.read(wiki_users.PATH)[0])
    except github.GitHubError as e:
        error = str(e)
    return render_template("admin/wiki_users.html", entries=entries, error=error)


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
        return redirect(url_for("wiki_admin.wiki_content"))

    rows = site.get("highlights", []) + [{"date": "", "title": "", "text": "", "done": False}] * EXTRA_ROWS
    return render_template("admin/wiki_content.html", site=site, rows=rows, error=None)
