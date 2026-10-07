"""Accounts: register, confirm e-mail, sign in/out, reset password."""
import re

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import mail
from .db import get_db, now
from .security import login_required, make_token, read_token

bp = Blueprint("auth", __name__, url_prefix="/account")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VERIFY_MAX_AGE = 3 * 24 * 3600      # 3 days
RESET_MAX_AGE = 2 * 3600            # 2 hours


def _is_admin_email(email):
    return email.lower() in mail.admin_addresses()


def _safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else url_for("main.calendar")


def _send_verification(user):
    token = make_token("verify", user["id"])
    mail.send(user["email"], "Confirm your e-mail address", "verify",
              name=user["name"], link=url_for("auth.verify", token=token, _external=False))


@bp.route("/register", methods=["GET", "POST"])
def register():
    form = {"name": "", "email": "", "institute": ""}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in form}
        form["email"] = form["email"].lower()
        password = request.form.get("password", "")
        errors = []
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
            return render_template("auth/check_email.html", email=form["email"])
        for e in errors:
            flash(e, "error")
    return render_template("auth/register.html", form=form)


@bp.route("/verify/<token>")
def verify(token):
    uid = read_token("verify", token, VERIFY_MAX_AGE)
    if uid is None:
        flash("This confirmation link is invalid or expired. Sign in to get a new one.", "error")
        return redirect(url_for("auth.login"))
    db = get_db()
    db.execute("UPDATE users SET verified = 1 WHERE id = ?", (uid,))
    db.commit()
    flash("E-mail confirmed. You can now sign in.", "ok")
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], request.form.get("password", "")):
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
    return render_template("auth/login.html", email=email)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Signed out.", "ok")
    return redirect(url_for("main.calendar"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            # the token includes part of the current hash, so it stops working once used
            token = make_token("reset", [user["id"], user["password_hash"][-12:]])
            mail.send(user["email"], "Reset your password", "reset",
                      name=user["name"], link=url_for("auth.reset", token=token))
        # same answer whether or not the address exists
        flash("If that address has an account, a reset link is on its way.", "ok")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot.html")


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    data = read_token("reset", token, RESET_MAX_AGE)
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (data[0],)).fetchone() if data else None
    if user is None or user["password_hash"][-12:] != data[1]:
        flash("This reset link is invalid, expired or already used.", "error")
        return redirect(url_for("auth.forgot"))
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
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html")


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
            return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html")
