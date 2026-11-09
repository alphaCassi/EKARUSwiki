# EKARUSwiki server

The active part of EKARUS. The wiki pages (`docs/`) are static and published by GitHub Pages
for the team; this server does everything else:

| Address | What |
|---|---|
| `/` | **EKARUS Observation Schedule** site: this server's address *is* the schedule site. Every page needs signing in first |
| `/dashboard` | Observers' dashboard: their proposals and statuses, upcoming nights |
| `/proposals/new`, `/proposals/<n>` | Submit and follow a proposal |
| `/info/telescope`, `/info/bench`, `/info/team` | Wiki pages shown to signed-in observers (read live from the wiki) |
| `/account/…` | Sign-in (see below), observer registration, password reset |
| `/admin/` | **EKARUSwiki admin**: overview, messages, team members, wiki home page content, observer accounts |
| `/admin/schedule/…` | Observation schedule, admin side: proposals to review, nights |
| `/api/…` | Called by the wiki: team sign-in check, contact form, access requests |

Old links to `/schedule/…` are redirected. All sign-ins end when the browser is closed.

## Who signs in how

| Who | How |
|---|---|
| **EKARUS team** (Admin → Team members, approved access requests, the wiki's `users.js`, and all `ADMIN_EMAILS`) | **E-mail only, no password**, on the wiki's sign-in page or this server's. |
| **Admins** (`ADMIN_EMAILS`) | Tick **Sign in as admin** on the wiki's sign-in page: e-mail, then the **admin password** (`ADMIN_PASSWORD` in `.env`). |
| **External observers** | **Register** on the schedule site with a password, confirm their e-mail, then use the calendar, dashboard, proposals and the Telescope / Bench / Team pages. |

Approving a wiki **access request** (Admin → Messages) adds the person to the team list and
e-mails them; no GitHub token is needed. With `GITHUB_TOKEN`, the wiki's own list `users.js`
(used only when this server is off) is updated as well.

## Folder layout

```
ekaruswiki/__init__.py      App setup, settings (read from .env), entry page
ekaruswiki/accounts.py      Sign-in links for the team; observer register, confirm, sign in/out, reset
ekaruswiki/admin.py         Admin: overview, messages, team members, wiki content, observer accounts
ekaruswiki/team.py          Who is on the EKARUS team (sign-in without password)
ekaruswiki/wiki_pages.py    Telescope / Bench / Team pages read from the wiki for observers
ekaruswiki/api.py           /api/contact for the wiki's forms (CORS, spam trap, rate limit)
ekaruswiki/schedule/        Observation schedule (the site at /)
    views.py                  calendar, dashboard, info pages, new proposal, withdraw
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
Dockerfile, docker-compose.yml   Docker setup: see LINUX_SETUP.md
deploy/                     systemd and nginx examples (alternative to Docker)
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

*Home page content* (and the offline copy of the team list) commit to the wiki repository:

1. GitHub: profile picture → Settings → Developer settings → Personal access tokens →
   **Fine-grained tokens** → Generate new token. Repository access: only `EKARUSwiki`.
   Permissions → Repository → **Contents: Read and write**.
2. `.env`: `GITHUB_TOKEN=<token>`, `GITHUB_REPO=alphaCassi/EKARUSwiki`,
   `WIKI_URL=https://alphacassi.github.io/EKARUSwiki/`. Restart the server.

Keep the token only in `.env` (never in git).

## Permanent setup on Linux

See **LINUX_SETUP.md**: Docker plus a free fixed address with Tailscale Funnel.

## Deploy on a Linux server without Docker

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
