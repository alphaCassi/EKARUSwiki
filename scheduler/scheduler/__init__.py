"""EKARUS observing scheduler: proposals for available nights, reviewed by the admin."""
import os
from datetime import date

from flask import Flask

from . import db, security


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "scheduler.sqlite3"),
        # Comma-separated list. These addresses become admins when they register or log in.
        ADMIN_EMAILS=os.environ.get("ADMIN_EMAILS", "oleksandra.rebrysh@inaf.it"),
        # Public address of this app, used in e-mail links.
        BASE_URL=os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/"),
        WIKI_URL=os.environ.get("WIKI_URL", ""),
        # E-mail: if SMTP_HOST is empty, messages are saved as .eml files in instance/outbox.
        SMTP_HOST=os.environ.get("SMTP_HOST", ""),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
        SMTP_USER=os.environ.get("SMTP_USER", ""),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""),
        SMTP_STARTTLS=os.environ.get("SMTP_STARTTLS", "1") == "1",
        MAIL_FROM=os.environ.get("MAIL_FROM", "EKARUS scheduler <no-reply@example.org>"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "1") == "1",
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    security.init_app(app)

    from . import auth, main, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)

    @app.template_filter("nicedate")
    def nicedate(value):
        d = date.fromisoformat(value[:10])
        return d.strftime("%a %d %b %Y")

    @app.template_filter("monthname")
    def monthname(value):
        return date.fromisoformat(value[:7] + "-01").strftime("%B %Y")

    @app.template_filter("shortdate")
    def shortdate(value):
        return value[:16].replace("T", " ")

    return app
