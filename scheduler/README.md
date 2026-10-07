# EKARUS observation scheduler

A small web app for requesting EKARUS observing nights.

- **Observers** register (with e-mail confirmation), see which nights are open, and submit a
  proposal: case, targets, and the nights they can use. They follow its status online.
- **The admin** opens nights in the calendar, reviews proposals, and accepts (choosing which of
  the requested nights to allocate) or rejects with a message.
- **E-mails are automatic**: account confirmation, password reset, receipt to the PI,
  alert to the admin for every new or withdrawn proposal, and the decision to the PI.

It needs a server that runs Python. GitHub Pages can't host it, because it stores accounts and
proposals and sends e-mail. The wiki's "Observation Schedule" button opens it in a new tab.

## Folder layout

```
scheduler/__init__.py     App setup and settings (read from environment variables)
scheduler/schema.sql      Database tables: users, nights, proposals, targets, requests, history
scheduler/db.py           SQLite connection; "flask init-db" command
scheduler/security.py     Sign-in checks, admin check, CSRF protection, signed e-mail links
scheduler/mail.py         Sending e-mail (SMTP), or saving it to instance/outbox/ if no SMTP is set
scheduler/auth.py         Register, confirm e-mail, sign in/out, reset password, profile
scheduler/main.py         Public calendar, new proposal, my proposals, withdraw
scheduler/admin.py        Review and decide, cancel an allocation, open/close nights, users
scheduler/templates/      Page templates; templates/email/ holds the e-mail texts
scheduler/static/         CSS, JS, fonts and logo (same style as the wiki)
tests/test_flow.py        End-to-end tests (no server needed)
wsgi.py                   Production entry point (gunicorn)
deploy/                   systemd service and nginx (HTTPS) examples
.env.example              All settings, with explanations
```

Data lives in `instance/scheduler.sqlite3` (created automatically). Back up that file.

## Proposal life cycle

```
submitted ──► accepted ──► (cancelled by admin → nights reopen)
    │
    ├──────► rejected   (reason required, sent to the PI)
    └──────► withdrawn  (by the PI, only before review)
```

Nights are `open` (can be requested), `closed` (not offered) or `booked` (allocated to an
accepted proposal). Several proposals can request the same open night; once one is accepted
for it, the night is booked and can't be allocated again.

## Run the tests

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Deploy (institute server)

1. Copy this folder to the server, e.g. `/opt/ekarus-scheduler`, create the virtualenv and
   install `requirements.txt`.
2. `cp .env.example .env` and fill it in: a random `SECRET_KEY`, `BASE_URL`, and the SMTP
   settings from your mail provider (ask INAF IT for an SMTP account for automatic mail).
3. Install `deploy/ekarus-scheduler.service` (gunicorn) and `deploy/nginx.conf` (HTTPS).
4. Register on the site with the admin address in `ADMIN_EMAILS`; you get the Admin menu.
5. Put the app's address in the wiki: `schedulerUrl` in `docs/assets/js/config.js`.

Until `SMTP_HOST` is set, e-mails are saved as `.eml` files in `instance/outbox/`, so the whole
workflow can be checked first.

## Not included yet

Editing a proposal after submission (the PI withdraws and resubmits), file attachments,
calendar export (.ics) and rate limiting of sign-in attempts.
