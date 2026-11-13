"""EKARUSwiki admin: overview, messages from the wiki, wiki sign-in list, editable home
content and server accounts. The observation schedule has its own admin section
(schedule/admin.py) linked from here.

Changes to the wiki are committed to its GitHub repository (see github.py); GitHub Pages
publishes them within a minute or two.
"""
import json
import re
from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from . import github, mail, team, wiki_users
from .db import get_db, now
from .security import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

SITE_PATH = "docs/data/site.json"
EXTRA_ROWS = 3
MAX_IMAGE_BYTES = 3_000_000


def new_messages():
    return get_db().execute("SELECT COUNT(*) FROM messages WHERE status = 'new'").fetchone()[0]


@bp.app_context_processor
def inject_counts():
    from .security import is_admin_session
    if is_admin_session():
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
        "team": len(team.all_members()),
    }
    return render_template("admin/overview.html", c=counts, github_ok=github.configured())


# ---------------------------------------------------------------- sign-in log
@bp.route("/signins")
@admin_required
def signins():
    show = request.args.get("show", "all")
    sql = "SELECT * FROM signin_log"
    if show == "failed":
        sql += " WHERE ok = 0"
    rows = get_db().execute(sql + " ORDER BY id DESC LIMIT 300").fetchall()
    failed_24h = get_db().execute(
        "SELECT COUNT(*) FROM signin_log WHERE ok = 0 AND at >= datetime('now', '-1 day')").fetchone()[0]
    return render_template("admin/signins.html", rows=rows, show=show, failed_24h=failed_24h)


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
    signed = {r["email"] for r in db.execute("SELECT email FROM users WHERE password_hash LIKE '!%' OR is_admin = 1")}
    added = {r["email"]: r["added_at"] for r in db.execute("SELECT email, added_at FROM team")}
    members = [{"email": e, "name": n, "source": src, "added": added.get(e, ""),
                "signed_in": bool(e and e in signed)} for e, n, src in team.all_members()]
    return render_template("admin/team.html", members=members, admins=mail.admin_addresses(),
                           github_ok=github.configured())


# ---------------------------------------------------------------- home page content
def _image_upload(field):
    """Read an uploaded image from the form. Returns (bytes, extension) or (None, None)."""
    f = request.files.get(field)
    if not f or not f.filename:
        return None, None
    data = f.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"{f.filename} is larger than {MAX_IMAGE_BYTES // 1_000_000} MB; please resize it.")
    if data[:3] == b"\xff\xd8\xff":
        ext = "jpg"
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        ext = "webp"
    else:
        raise ValueError(f"{f.filename} isn't a JPEG, PNG or WebP image.")
    return data, ext


def _save_image(data, ext, base):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:40] or "image"
    rel = f"assets/img/highlights/{stamp}-{slug}.{ext}"
    github.write_bytes("docs/" + rel, data, f"Add home page picture {rel} (by {g.user['name']} via admin page)")
    return rel


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
        try:
            # main picture
            image = site.get("image") or {}
            if request.form.get("main_remove"):
                image = {}
            data, ext = _image_upload("main_image")
            if data:
                image = {"src": _save_image(data, ext, "main")}
            if image:
                image["alt"] = request.form.get("main_alt", "").strip()[:200]
                image["caption"] = request.form.get("main_caption", "").strip()[:300]

            dates, titles = request.form.getlist("h_date"), request.form.getlist("h_title")
            texts, dones = request.form.getlist("h_text"), request.form.getlist("h_done")
            other = {f"{k}_{l}": request.form.getlist(f"h_{k}_{l}") for k in ("title", "text") for l in ("it", "fr")}
            kept, alts = request.form.getlist("h_image_keep"), request.form.getlist("h_alt")
            removes = set(request.form.getlist("h_image_remove"))
            highlights = []
            for i in range(len(titles)):
                row = {"date": dates[i].strip()[:60], "title": titles[i].strip()[:200],
                       "text": texts[i].strip()[:1500], "done": dones[i] == "yes"}
                for key, values in other.items():              # Italian and French versions
                    v = (values[i] if i < len(values) else "").strip()[:1500 if key.startswith("text") else 200]
                    if v:
                        row[key] = v
                src = kept[i] if i < len(kept) else ""
                if str(i) in removes:
                    src = ""
                data, ext = _image_upload(f"h_image_{i}")
                if data:
                    src = _save_image(data, ext, row["title"] or "highlight")
                if src:
                    row["image"] = {"src": src, "alt": (alts[i] if i < len(alts) else "").strip()[:200]}
                if row["title"] or row["text"]:
                    highlights.append(row)
            new = {"banner": request.form.get("banner", "").strip()[:200], "highlights": highlights}
            for l in ("it", "fr"):
                v = request.form.get(f"banner_{l}", "").strip()[:200]
                if v:
                    new[f"banner_{l}"] = v
            if image:
                new["image"] = image
            github.write(SITE_PATH, json.dumps(new, ensure_ascii=False, indent=2) + "\n", sha,
                         f"Update home page content (by {g.user['name']} via admin page)")
            flash("Saved. The wiki shows the change within a minute or two.", "ok")
        except ValueError as e:
            flash(str(e), "error")
        except github.GitHubError as e:
            flash(str(e), "error")
        return redirect(url_for("admin.wiki_content"))

    rows = site.get("highlights", []) + [{"date": "", "title": "", "text": "", "done": False}] * EXTRA_ROWS
    return render_template("admin/wiki_content.html", site=site, rows=rows, error=None)
