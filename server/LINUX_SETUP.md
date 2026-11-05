# EKARUSwiki server on Linux, with Docker

This sets the server up for continuous use on a Linux PC that stays on:

- **Docker** runs the server, restarts it after crashes and reboots.
- **Tailscale Funnel** (free) gives it a fixed public `https://…ts.net` address, so the
  observation schedule site has its own permanent address and the wiki can reach it.

Commands are for Ubuntu/Debian; other distributions differ only in package installation.
`~/EKARUSwiki` is used as the folder of the repository.

---

## 1. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```
Log out and back in (so `docker` works without `sudo`), then check:
```bash
docker run --rm hello-world
docker compose version
```

## 2. Get the code and your settings

```bash
cd ~
git clone https://github.com/alphaCassi/EKARUSwiki.git
cd EKARUSwiki/server
```

Copy from your Windows test setup into `~/EKARUSwiki/server/`:

| What | Why |
|---|---|
| `.env` | Your settings: `SECRET_KEY`, `ADMIN_PASSWORD`, SMTP (Gmail app password), `GITHUB_TOKEN` |
| `instance/` folder | Optional: keeps accounts, team list, nights, proposals and messages |

Without them: `cp .env.example .env`, fill it in, and the database starts empty.

Make sure the data folder belongs to you (the container runs as user 1000):
```bash
mkdir -p instance && sudo chown -R 1000:1000 instance
```

## 3. Install Tailscale and get the permanent address

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Open the link it prints and sign in (free personal plan). Then publish port 5000:
```bash
sudo tailscale funnel --bg 5000
```
The first time it may print a link to **enable HTTPS and Funnel** in the Tailscale admin
console: open it, approve, and run the command again. It then shows your address, e.g.
```
https://yourpc.tail1234.ts.net/
```
`--bg` keeps it active, also after reboots (the Tailscale service starts with the system).
Check any time with `tailscale funnel status`.

## 4. Settings in `.env`

Set (or change) these lines; keep the rest:
```
BASE_URL=https://yourpc.tail1234.ts.net
WIKI_URL=https://alphacassi.github.io/EKARUSwiki/
PROXY_FIX=1
SESSION_COOKIE_SECURE=1
```
No `/` at the end of `BASE_URL`. No quotes around values.

## 5. Start the server

```bash
cd ~/EKARUSwiki/server
docker compose up -d --build
docker compose ps
```
`ps` should show the server as **running** (after a minute: **healthy**).
Open `https://yourpc.tail1234.ts.net` from any device: you should see the EKARUS
Observation schedule.

## 6. Point the wiki to it (once)

In `docs/assets/js/config.js`:
```js
serverUrl: "https://yourpc.tail1234.ts.net",
```
Commit and push. This address doesn't change any more.

## 7. Keep the PC awake

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```
(Undo with `unmask` and the same names.)

---

## Everyday commands

Run them in `~/EKARUSwiki/server`.

| What | Command |
|---|---|
| Status | `docker compose ps` |
| Live log (errors, e-mail problems) | `docker compose logs -f server` |
| After changing `.env` | `docker compose up -d` |
| After updating the code | `git pull && docker compose up -d --build` |
| Stop / start | `docker compose down` / `docker compose up -d` |
| Read outbox e-mails (no SMTP set) | `ls instance/outbox/` and open the newest `.eml` |
| Back up the data | copy the `instance/` folder (e.g. `tar czf ekaruswiki-backup.tgz instance`) |

Docker starts the server again by itself after a reboot (`restart: unless-stopped`).

## Quick test without Tailscale

For a short test, a temporary Cloudflare address (it changes every restart):
```bash
docker compose --profile quicktunnel up -d
docker compose logs quicktunnel      # the https://….trycloudflare.com address
```
Put that address in `BASE_URL` (then `docker compose up -d`) and in the wiki's `serverUrl`.

## Troubleshooting

| Problem | Check |
|---|---|
| Page doesn't load at the ts.net address | `docker compose ps` (running?), `tailscale funnel status` (port 5000?) |
| `Permission denied` on `instance/` in the log | `sudo chown -R 1000:1000 instance` |
| Sign-in link or confirmation e-mails don't arrive | `docker compose logs server` shows the SMTP error; check the SMTP lines in `.env` |
| Links in e-mails point to the wrong address | `BASE_URL` in `.env`, then `docker compose up -d` |
| The wiki says the server isn't connected | `serverUrl` in `docs/assets/js/config.js`, pushed, reloaded with Ctrl+F5 |

