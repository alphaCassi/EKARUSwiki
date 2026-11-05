"""Endpoints called from the wiki (a different site), so they answer with CORS headers.

POST /api/signin-link {email, next}  e-mail a sign-in link to a team member (see accounts.py)
POST /api/contact   {kind: "contact"|"access", name, email, topic, page, message, website}
  - "contact": a change request for the wiki
  - "access":  a request to be registered on the wiki
  - "website" is a hidden field people never fill in; bots do (spam trap)
The message is stored for the admin page and e-mailed to the admins.
"""
import hashlib
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, request

from . import mail
from .db import get_db, now

bp = Blueprint("api", __name__, url_prefix="/api")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_PER_HOUR = 5
LIMITS = {"name": 120, "email": 200, "topic": 120, "page": 200, "message": 5000}
TOPICS = ["Content correction", "New content", "Design / layout", "Broken link", "Other"]


def allowed_origins():
    origins = set()
    wiki = current_app.config.get("WIKI_URL", "")
    if wiki:
        u = urlsplit(wiki)
        origins.add(f"{u.scheme}://{u.netloc}")
    extra = current_app.config.get("CORS_ORIGINS", "")
    origins.update(o.strip().rstrip("/") for o in extra.split(",") if o.strip())
    return origins


@bp.after_request
def cors(resp):
    origin = request.headers.get("Origin", "")
    if origin and origin in allowed_origins():
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Max-Age"] = "3600"
        resp.headers["Vary"] = "Origin"
    return resp


def fail(msg, code=400):
    return jsonify(ok=False, error=msg), code


@bp.route("/contact", methods=["POST", "OPTIONS"])
def contact():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    if data.get("website"):                      # spam trap filled in: pretend success
        return jsonify(ok=True)

    kind = data.get("kind", "contact")
    if kind not in ("contact", "access"):
        return fail("Unknown request type.")
    f = {k: str(data.get(k, "")).strip()[:n] for k, n in LIMITS.items()}
    f["email"] = f["email"].lower()
    if not f["name"]:
        return fail("Enter your name.")
    if not EMAIL_RE.match(f["email"]):
        return fail("Enter a valid e-mail address.")
    if kind == "contact" and not f["message"]:
        return fail("Write what you'd like to change.")
    if kind == "contact" and f["topic"] not in TOPICS:
        f["topic"] = "Other"

    db = get_db()
    ip_hash = hashlib.sha256((request.remote_addr or "").encode()).hexdigest()[:16]
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0).isoformat()
    recent = db.execute("SELECT COUNT(*) FROM messages WHERE ip_hash = ? AND created_at >= ?",
                        (ip_hash, since)).fetchone()[0]
    if recent >= MAX_PER_HOUR:
        return fail("Too many messages in a short time. Please try again in an hour.", 429)

    cur = db.execute(
        "INSERT INTO messages (created_at, kind, name, email, topic, page, body, ip_hash)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (now(), kind, f["name"], f["email"], f["topic"], f["page"], f["message"], ip_hash))
    db.commit()
    msg = db.execute("SELECT * FROM messages WHERE id = ?", (cur.lastrowid,)).fetchone()

    subject = (f"Wiki access request from {f['name']}" if kind == "access"
               else f"Wiki change request: {f['topic']}")
    mail.send(mail.admin_addresses(), subject, "message_admin", reply_to=f["email"], m=msg,
              link=f"/admin/messages/{msg['id']}")
    return jsonify(ok=True)


@bp.route("/signin-link", methods=["POST", "OPTIONS"])
def signin_link():
    """Wiki sign-in page: e-mail a one-time sign-in link to a team member (no password)."""
    if request.method == "OPTIONS":
        return "", 204
    from .accounts import send_signin_link
    data = request.get_json(silent=True) or {}
    sent, error = send_signin_link(str(data.get("email", ""))[:200], str(data.get("next", ""))[:500])
    if sent:
        return jsonify(ok=True)
    return fail(error, 429 if "minute ago" in error else 400)
