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
    app.jinja_env.globals["is_admin_session"] = is_admin_session
    from .names import split_name
    app.jinja_env.globals["split_name"] = split_name
    from .schedule.files import expiry_date
    app.jinja_env.globals["file_expiry"] = expiry_date


def load_user():
    uid = session.get("user_id")
    g.user = None
    if uid is not None:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if g.user is None:
            session.clear()


def _admin_active():
    """Admin access from the admin password, still within ADMIN_IDLE_MINUTES of the last admin page."""
    import time
    from flask import current_app
    t = session.get("admin_ok")
    if not isinstance(t, (int, float)) or isinstance(t, bool):
        session.pop("admin_ok", None)
        return False
    if time.time() - t > current_app.config["ADMIN_IDLE_MINUTES"] * 60:
        session.pop("admin_ok", None)
        return False
    return True


def is_admin_session():
    """True only for an admin address that entered the admin password and is still active."""
    from . import mail
    return (getattr(g, "user", None) is not None and _admin_active()
            and g.user["email"] in mail.admin_addresses())


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if request.path != "/":
                flash("Sign in to continue.", "info")
            return redirect(url_for("accounts.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Admin pages: an address in ADMIN_EMAILS that typed the admin password, still active."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        import time
        from . import mail
        if g.user is not None and g.user["email"] not in mail.admin_addresses():
            abort(403)
        if g.user is None or not _admin_active():
            return redirect(url_for("accounts.admin_signin", next=request.path))
        session["admin_ok"] = time.time()           # still working in the admin pages
        return view(*args, **kwargs)
    return wrapped


# ---------- CSRF: every POST form carries a per-session token
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def check_csrf():
    # /api/ is called cross-site by the wiki without cookies; it has its own checks
    if request.path.startswith("/api/"):
        return
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
