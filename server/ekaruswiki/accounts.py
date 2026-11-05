"""Accounts.

- EKARUS team members (team.py) never need a password: they get an e-mail sign-in link,
  from the wiki's sign-in page or from this server's sign-in page.
- External observers register here with a password (observation schedule only).
"""
import base64
import json
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import mail, team
from .db import get_db, now
from .security import login_required, make_token, read_token

bp = Blueprint("accounts", __name__, url_prefix="/account")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VERIFY_MAX_AGE = 3 * 24 * 3600      # 3 days
RESET_MAX_AGE = 2 * 3600            # 2 hours
MAGIC_MAX_AGE = 30 * 60             # sign-in links work for 30 minutes, once
MAGIC_RESEND_SECONDS = 60           # at most one link per minute per address


def _is_admin_email(email):
    return email.lower() in mail.admin_addresses()


def _safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else url_for("schedule.calendar")


def _send_verification(user):
    token = make_token("verify", user["id"])
    mail.send(user["email"], "Confirm your e-mail address", "verify",
              name=user["name"], link=url_for("accounts.verify", token=token, _external=False))


@bp.route("/register", methods=["GET", "POST"])
def register():
    form = {"name": "", "email": "", "institute": ""}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in form}
        form["email"] = form["email"].lower()
        password = request.form.get("password", "")
        errors = []
        if form["email"] and team.is_team(form["email"]):
            flash("You're on the EKARUS team, so you don't need to register or use a password: "
                  "sign in with an e-mail link instead.", "info")
            return redirect(url_for("accounts.login", email=form["email"]))
        if not form["name"]:
            errors.append("Enter your name.")
        if not EMAIL_RE.match(form["email"]):
            errors.append("Enter a valid e-mail address.")
        if len(password) < 10:
            errors.append("Use a password of at least 10 characters.")
        if password != request.form.get("password2", ""):
            errors.append("The two passwords don't match.")
        db = get_db()
        if not errors and db.execute("SELECT 1 FROM users WHERE email = ?", (form["email"],)).fetchone():
            errors.append("An account with this e-mail already exists. Sign in or reset your password.")
        if not errors:
            cur = db.execute(
                "INSERT INTO users (email, name, institute, password_hash, is_admin, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (form["email"], form["name"], form["institute"], generate_password_hash(password),
                 int(_is_admin_email(form["email"])), now()))
            db.commit()
            user = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
            _send_verification(user)
            return render_template("accounts/check_email.html", email=form["email"])
        for e in errors:
            flash(e, "error")
    return render_template("accounts/register.html", form=form)


@bp.route("/verify/<token>")
def verify(token):
    uid = read_token("verify", token, VERIFY_MAX_AGE)
    if uid is None:
        flash("This confirmation link is invalid or expired. Sign in to get a new one.", "error")
        return redirect(url_for("accounts.login"))
    db = get_db()
    db.execute("UPDATE users SET verified = 1 WHERE id = ?", (uid,))
    db.commit()
    flash("E-mail confirmed. You can now sign in.", "ok")
    return redirect(url_for("accounts.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or user["password_hash"].startswith("!") or \
                not check_password_hash(user["password_hash"], request.form.get("password", "")):
            flash("E-mail or password is wrong.", "error")
        elif not user["verified"]:
            _send_verification(user)
            flash("Confirm your e-mail first. We've sent you a new confirmation link.", "error")
        else:
            # keep admin rights in sync with ADMIN_EMAILS
            is_admin = int(_is_admin_email(user["email"]))
            if is_admin != user["is_admin"]:
                db.execute("UPDATE users SET is_admin = ? WHERE id = ?", (is_admin, user["id"]))
                db.commit()
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(_safe_next(request.args.get("next")))
    return render_template("accounts/login.html", email=email or request.args.get("email", ""))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Signed out.", "ok")
    return redirect(url_for("home"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            # the token includes part of the current hash, so it stops working once used
            token = make_token("reset", [user["id"], user["password_hash"][-12:]])
            mail.send(user["email"], "Reset your password", "reset",
                      name=user["name"], link=url_for("accounts.reset", token=token))
        # same answer whether or not the address exists
        flash("If that address has an account, a reset link is on its way.", "ok")
        return redirect(url_for("accounts.login"))
    return render_template("accounts/forgot.html")


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    data = read_token("reset", token, RESET_MAX_AGE)
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (data[0],)).fetchone() if data else None
    if user is None or user["password_hash"][-12:] != data[1]:
        flash("This reset link is invalid, expired or already used.", "error")
        return redirect(url_for("accounts.forgot"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 10:
            flash("Use a password of at least 10 characters.", "error")
        elif password != request.form.get("password2", ""):
            flash("The two passwords don't match.", "error")
        else:
            db.execute("UPDATE users SET password_hash = ?, verified = 1 WHERE id = ?",
                       (generate_password_hash(password), user["id"]))
            db.commit()
            flash("Password changed. Sign in with the new one.", "ok")
            return redirect(url_for("accounts.login"))
    return render_template("accounts/reset.html")


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        institute = request.form.get("institute", "").strip()
        if not name:
            flash("Enter your name.", "error")
        else:
            db = get_db()
            db.execute("UPDATE users SET name = ?, institute = ? WHERE id = ?", (name, institute, g.user["id"]))
            db.commit()
            flash("Profile saved.", "ok")
            return redirect(url_for("accounts.profile"))
    return render_template("accounts/profile.html")


# ---------------------------------------------------------------- e-mail sign-in links (team)
def _wiki_next(target):
    """Only send people back to this server or to the wiki."""
    wiki = current_app.config.get("WIKI_URL", "")
    if target and wiki and target.startswith(wiki.rstrip("/")):
        return target
    return _safe_next(target)


def send_signin_link(email, next_url=""):
    """E-mail a one-time sign-in link to a team member. Returns (sent, error_message)."""
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Enter a valid e-mail address."
    if not team.is_team(email):
        return False, "This address isn't on the EKARUS team list. Request access, or register as an observer."
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        cur = db.execute(
            "INSERT INTO users (email, name, institute, password_hash, is_admin, verified, created_at)"
            " VALUES (?, ?, '', '!no-password', ?, 1, ?)",
            (email, team.team_name(email), int(_is_admin_email(email)), now()))
        user = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    if user["magic_sent_at"]:
        last = datetime.fromisoformat(user["magic_sent_at"])
        if datetime.now(timezone.utc) - last < timedelta(seconds=MAGIC_RESEND_SECONDS):
            return False, "A link was sent less than a minute ago. Check your inbox (and spam)."
    nonce = secrets.token_hex(8)
    db.execute("UPDATE users SET magic_nonce = ?, magic_sent_at = ? WHERE id = ?", (nonce, now(), user["id"]))
    db.commit()
    token = make_token("magic", [user["id"], nonce])
    mail.send(email, "Your sign-in link", "signin_link", name=user["name"],
              link=url_for("accounts.magic", token=token, next=next_url or None))
    return True, ""


@bp.route("/email-link", methods=["POST"])
def email_link():
    sent, error = send_signin_link(request.form.get("email", ""), request.form.get("next", ""))
    if sent:
        return render_template("accounts/check_email.html", email=request.form.get("email", "").strip().lower(),
                               signin_link=True)
    flash(error, "error")
    return redirect(url_for("accounts.login", email=request.form.get("email", "")))


@bp.route("/magic/<token>")
def magic(token):
    data = read_token("magic", token, MAGIC_MAX_AGE)
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (data[0],)).fetchone() if data else None
    if user is None or not user["magic_nonce"] or user["magic_nonce"] != data[1]:
        flash("This sign-in link is invalid, expired or already used. Ask for a new one.", "error")
        return redirect(url_for("accounts.login"))
    is_admin = int(_is_admin_email(user["email"]))
    db.execute("UPDATE users SET magic_nonce = '', verified = 1, is_admin = ? WHERE id = ?", (is_admin, user["id"]))
    db.commit()
    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True

    target = _wiki_next(request.args.get("next", ""))
    wiki = current_app.config.get("WIKI_URL", "").rstrip("/")
    if wiki and target.startswith(wiki):
        # Tell the wiki (a static site) who signed in. It only uses this to show the pages and
        # the Admin button; everything protected is checked again here on the server.
        info = {"email": user["email"], "name": user["name"], "admin": bool(is_admin),
                "exp": int(time.time()) + 30 * 24 * 3600}
        blob = base64.urlsafe_b64encode(json.dumps(info).encode()).decode().rstrip("=")
        return redirect(target.split("#")[0] + "#ekarus-auth=" + blob)
    return redirect(target)
