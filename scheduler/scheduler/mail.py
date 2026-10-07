"""Outgoing e-mail.

With SMTP_HOST configured, messages are sent through that server.
Without it, each message is written to instance/outbox/ as an .eml file, so the
whole workflow can be tried before the mail server is set up.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from datetime import datetime

from flask import current_app, render_template


def admin_addresses():
    return [a.strip().lower() for a in current_app.config["ADMIN_EMAILS"].split(",") if a.strip()]


def send(to, subject, template, **context):
    """Render templates/email/<template>.txt and send it to one address or a list."""
    if isinstance(to, str):
        to = [to]
    cfg = current_app.config
    context.setdefault("base_url", cfg["BASE_URL"])
    body = render_template(f"email/{template}.txt", **context)

    msg = EmailMessage()
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = ", ".join(to)
    msg["Subject"] = f"[EKARUS] {subject}"
    msg["Message-ID"] = make_msgid(domain="ekarus")
    msg.set_content(body)

    if cfg["SMTP_HOST"]:
        try:
            with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20) as s:
                if cfg["SMTP_STARTTLS"]:
                    s.starttls(context=ssl.create_default_context())
                if cfg["SMTP_USER"]:
                    s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
                s.send_message(msg)
        except Exception:  # never break the user's action because mail failed
            current_app.logger.exception("Sending e-mail to %s failed", to)
            _save(msg)
    else:
        _save(msg)


def _save(msg):
    outbox = os.path.join(current_app.instance_path, "outbox")
    os.makedirs(outbox, exist_ok=True)
    name = datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".eml"
    with open(os.path.join(outbox, name), "wb") as f:
        f.write(bytes(msg))
    current_app.logger.info("E-mail saved to outbox/%s: %s", name, msg["Subject"])
