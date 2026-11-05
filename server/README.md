# EKARUSwiki server

The active part of the EKARUS wiki. The wiki pages (`docs/`) are static and published by
GitHub Pages; everything that has to receive, store or change something runs here:

| Address | What |
|---|---|
| `/` | Entry page (admins go straight to the admin overview) |
| `/account/…` | One account system for the whole server: register, confirm e-mail, sign in, reset password |
| `/admin/` | **EKARUSwiki admin**: overview with counts and links to every admin tool |
| `/admin/messages` | Change requests (wiki *Contact us*) and access requests (wiki sign-in page) |
| `/admin/wiki-users` | Who can sign in to the wiki (edits `docs/assets/js/users.js` on GitHub) |
| `/admin/wiki-content` | Wiki banner and highlights (edits `docs/data/site.json` on GitHub) |
| `/admin/accounts` | Accounts registered on this server |
| `/admin/schedule/…` | Observation schedule, admin side: proposals to review, nights |
| `/schedule/…` | Observation schedule for observers: calendar, proposals |
| `/api/contact` | Receives the wiki's forms |

Admins are the addresses in `ADMIN_EMAILS`. E-mails are sent automatically: account
confirmation, password reset, every new message or proposal to the admins, and decisions to
the observers.

## Folder layout

```
ekaruswiki/__init__.py      App setup, settings (read from .env), entry page
ekaruswiki/accounts.py      Accounts: register, confirm, sign in/out, reset, profile
ekaruswiki/admin.py         Wiki admin: overview, messages, wiki users, wiki content, accounts
ekaruswiki/api.py           /api/contact for the wiki's forms (CORS, spam trap, rate limit)
ekaruswiki/schedule/        Observation schedule module
    views.py                  calendar, new proposal, my proposals, withdraw
    admin.py                  review and decide, cancel allocations, open/close nights
ekaruswiki/db.py            SQLite database; schema.sql has the tables
ekaruswiki/mail.py          Sending e-mail (SMTP), or saving to instance/outbox/ without SMTP
ekaruswiki/github.py        Reading and committing wiki files through the GitHub API
ekaruswiki/wiki_users.py    Format of the wiki's users.js (hashed e-mails)
ekaruswiki/security.py      Sign-in checks, admin check, CSRF protection, signed links
ekaruswiki/templates/       Pages (accounts/, admin/, schedule/) and e-mail texts (email/)
ekaruswiki/static/          CSS, JS, fonts, logo
tests/                      End-to-end tests (no server needed; GitHub is faked)
wsgi.py                     Entry point; loads .env
deploy/                     systemd service and nginx (HTTPS) examples for a Linux server
.env.example                All settings, explained
```

Data lives in `instance/` (database and, without SMTP, the e-mail outbox). Back it up.
An existing `instance/scheduler.sqlite3` from before the rename is used as is.

## Run it on your computer (Windows, Git Bash)

One time:
```bash
cd /d/EKARUS/EKARUSwiki/EKARUSwiki/server
py -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env          # then edit .env
```

Every time:
```bash
cd /d/EKARUS/EKARUSwiki/EKARUSwiki/server
source .venv/Scripts/activate
python -m flask --app wsgi run --port 5000
```

If the folder is moved or renamed, delete `.venv` and create it again.

### Reachable from outside: Cloudflare quick tunnel

Put `cloudflared.exe` in this folder (it's ignored by git) and, in a second window:
```bash
./cloudflared.exe tunnel --url http://localhost:5000
```
Use the printed `https://….trycloudflare.com` address as `BASE_URL` in `.env` (restart the
server) and as `serverUrl` in `docs/assets/js/config.js` (commit and push). The address
changes every time the tunnel restarts.

### Reading e-mails without a mail server

```bash
py -c "import email,glob,os; f=max(glob.glob('instance/outbox/*.eml'),key=os.path.getmtime); print(email.message_from_binary_file(open(f,'rb')).get_payload(decode=True).decode())"
```

## Connect the wiki (GitHub token)

*Wiki users* and *Home page content* commit to the wiki repository:

1. GitHub: profile picture → Settings → Developer settings → Personal access tokens →
   **Fine-grained tokens** → Generate new token. Repository access: only `EKARUSwiki`.
   Permissions → Repository → **Contents: Read and write**.
2. `.env`: `GITHUB_TOKEN=<token>`, `GITHUB_REPO=alphaCassi/EKARUSwiki`,
   `WIKI_URL=https://alphacassi.github.io/EKARUSwiki/`. Restart the server.

Keep the token only in `.env` (never in git).

## Deploy on a Linux server

1. Copy this folder to e.g. `/opt/ekaruswiki-server`, create `.venv`, install `requirements.txt`.
2. Fill in `.env` (random `SECRET_KEY`, `BASE_URL`, SMTP account, GitHub token).
3. Install `deploy/ekaruswiki-server.service` (gunicorn) and `deploy/nginx.conf` (HTTPS).
4. Set `serverUrl` in the wiki to the server's address.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Not included yet

Editing a proposal after submission, attachments, calendar export (.ics), rate limiting of
sign-in attempts.
