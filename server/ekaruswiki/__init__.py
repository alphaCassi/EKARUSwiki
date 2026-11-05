"""EKARUSwiki server: the active part of the EKARUS wiki.

The wiki pages themselves are static (docs/, published by GitHub Pages). Everything that has
to receive, store or change something runs here:

  /account/...          one account system for the whole server
  /admin/...            EKARUSwiki admin: overview, messages, wiki users, wiki content, accounts
  /admin/schedule/...   observation schedule, admin side (proposals, nights)
  /schedule/...         observation schedule for observers (calendar, proposals)
  /api/contact          contact form and access requests sent from the wiki
"""
import os
from datetime import date

from flask import Flask, g, redirect, render_template, url_for

from . import db, security


def _default_database(instance_path):
    # Older installs called the database file scheduler.sqlite3: keep using it if it exists.
    old = os.path.join(instance_path, "scheduler.sqlite3")
    return old if os.path.exists(old) else os.path.join(instance_path, "ekaruswiki.sqlite3")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE") or _default_database(app.instance_path),
        # Comma-separated list. These addresses become admins when they register or sign in.
        ADMIN_EMAILS=os.environ.get("ADMIN_EMAILS", "oleksandra.rebrysh@inaf.it"),
        # Public address of this server, used in e-mail links.
        BASE_URL=os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/"),
        # Address of the published wiki (GitHub Pages).
        WIKI_URL=os.environ.get("WIKI_URL", ""),
        # E-mail: if SMTP_HOST is empty, messages are saved as .eml files in instance/outbox.
        SMTP_HOST=os.environ.get("SMTP_HOST", ""),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
        SMTP_USER=os.environ.get("SMTP_USER", ""),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
        SMTP_STARTTLS=os.environ.get("SMTP_STARTTLS", "1") == "1",
        MAIL_FROM=os.environ.get("MAIL_FROM", "EKARUSwiki <no-reply@example.org>"),
        # Wiki integration: the GitHub repository holding the wiki (docs/ folder) and a
        # fine-grained token with "Contents: read and write" on that repository only.
        GITHUB_REPO=os.environ.get("GITHUB_REPO", "alphaCassi/EKARUSwiki"),
        GITHUB_BRANCH=os.environ.get("GITHUB_BRANCH", "main"),
        GITHUB_TOKEN=os.environ.get("GITHUB_TOKEN", ""),
        # Extra sites allowed to send the contact form (comma-separated), e.g. http://localhost:8000
        CORS_ORIGINS=os.environ.get("CORS_ORIGINS", ""),
        # Behind nginx or a Cloudflare tunnel: trust its X-Forwarded-For header (rate limiting)
        PROXY_FIX=os.environ.get("PROXY_FIX", "0") == "1",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "1") == "1",
    )
    if test_config:
        app.config.update(test_config)

    if app.config["PROXY_FIX"]:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    security.init_app(app)

    from . import accounts, admin, api
    from .schedule import admin as schedule_admin, views as schedule_views
    app.register_blueprint(accounts.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(schedule_views.bp)
    app.register_blueprint(schedule_admin.bp)

    @app.route("/")
    def home():
        """Server entry page: admins go to the admin overview, everyone else to the schedule."""
        if g.user is not None and g.user["is_admin"]:
            return redirect(url_for("admin.overview"))
        return render_template("home.html")

    @app.template_filter("nicedate")
    def nicedate(value):
        return date.fromisoformat(value[:10]).strftime("%a %d %b %Y")

    @app.template_filter("monthname")
    def monthname(value):
        return date.fromisoformat(value[:7] + "-01").strftime("%B %Y")

    @app.template_filter("shortdate")
    def shortdate(value):
        return value[:16].replace("T", " ")

    return app
