"""Login, admin checks, CSRF protection and signed e-mail tokens."""
import functools
import secrets

from flask import abort, current_app, flash, g, redirect, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .db import get_db


def init_app(app):
    app.before_request(load_user)
    app.before_request(check_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token


def load_user():
    uid = session.get("user_id")
    g.user = None
    if uid is not None:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if g.user is None:
            session.clear()


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Sign in to continue.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @functools.wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not g.user["is_admin"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------- CSRF: every POST form carries a per-session token
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def check_csrf():
    if request.method == "POST" and not current_app.config.get("TESTING_NO_CSRF"):
        sent = request.form.get("csrf_token", "")
        if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
            abort(400, "The form expired. Go back, reload the page and try again.")


# ---------- Signed links for e-mail verification and password reset
def _serializer(purpose):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=f"ekarus-{purpose}")


def make_token(purpose, data):
    return _serializer(purpose).dumps(data)


def read_token(purpose, token, max_age):
    try:
        return _serializer(purpose).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
