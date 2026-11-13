# EKARUS wiki

Internal web pages for the EKARUS SCAO bench at the Copernico telescope.
Plain HTML, CSS and JavaScript: no build step, no frameworks, no external requests.

## Folder layout

```
index.html            Sign-in and "request access" page
home.html             Highlights / quick updates
pages/                One HTML file per navigation button
assets/css/main.css   All styling (colours, layout, light/dark, mobile)
assets/js/config.js   Site settings (admin e-mail, home page)
assets/js/users.js    Registered users (hashed e-mails) – edit with the tool below
assets/js/gate.js     Sends visitors who haven't signed in to index.html
assets/js/main.js     Sign-in, request access, sign-out, bench subsystem switching
assets/img/           Logo (dark version), favicon, schematics (WebP)
assets/img/partners/  Partner logos shown in the footer of every page
assets/fonts/         Barlow font files (SIL Open Font License)
tools/manage_users.py Add / remove / list registered users
.nojekyll             Tells GitHub Pages to publish the files as they are
```

## Editing pages

- **Navigation** is written in every page (left and right `<nav>` blocks). If you add or
  rename a page, update the nav in all HTML files. The current page is marked with
  `aria-current="page"`, which highlights its button.
- **Observation schedule → Calendar & proposals** opens the schedule site, which is the server's own address (`serverUrl`), in a new tab. Until `serverUrl` is set, it shows `pages/observation-schedule.html`.
- **Documentation** (`pages/documentation.html`): sections for results, design documents, logs and user guides; copy an `<li>` to add a document.
- **OAO school** button: opens two sub-buttons (Main webpage, Tutorials); the links are in the left `<nav>` of every page.
- **RTC & ICS** (`pages/bench.html`, panel `id="rtc-ics"`): replace the placeholder text, schematic and latency values.
- **DAO-EKARUS** button links straight to the DAO server; `pages/dao-ekarus.html` is kept but not linked.
- **Team photos** (`pages/team.html`): save each photo as `assets/img/team/<first-last>.webp` (about 300 px wide) and replace that person's `<span class="photo" ...></span>` with `<img class="photo" src="../assets/img/team/<first-last>.webp" width="300" height="360" alt="">`. The members table is below the diagram.
- **Partner logos**: the `<footer class="partners">` block at the bottom of every page.
- **Banner** (empty = hidden): edit it on the admin page ("Wiki home page"); it's stored in `data/site.json`.
- **Highlights**: add a new `<li>` at the top of the list in `home.html`.
- **Bench subsystems** (`pages/bench.html`): each subsystem is a
  `<section class="subsystem-panel" id="...">` with a matching
  `<button data-target="...">`. Panels can be linked directly, e.g.
  `pages/bench.html#wfs-channel`.
- **Images**: put them in `assets/img/` (WebP or JPEG, ideally under ~200 KB) and always
  set `width`, `height` and `alt`.

## Menus

- Left (project): Team, Telescope, Bench Architecture, DAO-EKARUS, Documentation.
- Right (activities): Observation schedule (Technical nights plan, and the Calendar & proposals
  site on the server), OAO school, Publications, To do's, Contact us.
- **Publications** (`pages/publications.html`): searchable list with filters (year, author, type,
  works that only mention EKARUS) and sorting. The entries are in `assets/js/publications-data.js`:
  copy one `{ ... }` block to add a publication (instructions at the top of the file).
- The menus are written in every page: when you add or rename a page, update them in all files.

## Signing in

Opening the wiki always shows the sign-in page. Team members type their e-mail and they're in
(no password) until they close the browser.
With the server connected (`serverUrl`), the server checks the team list; admins (ADMIN_EMAILS)
tick **Sign in as admin** on the sign-in page: after the e-mail they enter the admin password
on the server and land on the admin pages. If the
server can't be reached, the wiki uses its own list (`assets/js/users.js`).

## Admin, contact form and editable content

These need the EKARUSwiki server (`server/` folder) to be running and `serverUrl` set in
`assets/js/config.js`; see `server/README.md`.

- **Contact us** (`pages/contact.html`) and **Request access** (`index.html`) send their message to
  the server, which stores it on the admin page and e-mails the admins. No mail program is used.
- Admins open the admin pages with **Sign in as admin** on the sign-in page (`serverUrl` + `/admin/`).
- The banner and the Highlights come from `data/site.json`, which the admin page edits. The text
  written in the HTML pages is only a fallback (e.g. when a page is opened from disk).

## To-do list

The To-do page reads its list live from the Google spreadsheet linked at the bottom of
`pages/todo.html` (the link with `data-todo-file`). Edit the spreadsheet and the page shows the change
the next time it's opened (and every 2 minutes while it stays open). To use another spreadsheet,
change only that link.

The spreadsheet must be a Google Sheets file (not an uploaded .xlsx) shared as "Anyone with the
link". The first sheet is read, or the one given by `gid=` in the link. Columns recognised: Task,
Owner, Due, Status and, if filled in, Notes; "Done" in Status shows the row as done. The rows
written in `todo.html` are shown only if the spreadsheet can't be read.

## Publishing on GitHub Pages

1. This folder is `docs/` in the EKARUS repository; push the repository to the `main` branch.
2. Repository **Settings → Pages → Build and deployment**: Source "Deploy from a branch",
   branch `main`, folder **`/docs`** (so only the wiki pages are published, not the server code).
3. The site appears at `https://<user-or-org>.github.io/<repository>/` after a minute or two.

You can also open `docs/index.html` directly from disk to preview; no server is needed.

## Registering users

1. **One-time setup:** set `adminEmail` in `assets/js/config.js`, then register yourself:
   `python tools/manage_users.py add you@inaf.it --note "admin"`
2. **A colleague asks for access:** on the sign-in page they open "Request access" and send
   the pre-filled e-mail to the admin address.
3. **The admin registers them:**
   ```
   python tools/manage_users.py add colleague@inaf.it --note "initials"
   git add assets/js/users.js && git commit -m "Register user" && git push
   ```
4. Reply to the colleague: they can sign in with that address once GitHub has republished.

Other commands: `remove <email>`, `check <email>`, `list`.
Sign-in is remembered per browser until the user presses "Sign out".

## Important: this is not real access protection

GitHub Pages publishes every file in the repository to anyone with the URL, so:

- page contents can be read without signing in (by fetching the files directly or
  disabling JavaScript);
- the hashed e-mails in `users.js` can be matched against guessed addresses.

Treat the sign-in as a doorbell for the team, and don't put confidential material on the
site. If restricted access is needed later, the same files can be moved without changes to
a host that checks identity before serving any page, for example GitLab Pages with access
control (only project members can view) or Cloudflare Pages behind Cloudflare Access
(login by one-time code sent to a registered e-mail). Then `gate.js`, `users.js` and the
sign-in form can be dropped.

## Languages (English, Italiano, Français)

The EN / IT / FR buttons at the top right switch the language; the choice is kept in that
browser. On a first visit the wiki follows the browser's language. French pages show a note that
the French translation was made with AI, with a contact for corrections.

- **Content pages** (Team, Telescope, Bench Architecture, Documentation, Technical nights plan,
  DAO-EKARUS, Observation schedule) hold three blocks one after the other inside `<main>`:
  `<div data-lang-block="en">`, `"it"` and `"fr"`, each between `<!-- lang:xx -->` comments.
  Edit the text of each language in its own block. Inside the Italian and French blocks the `id`s
  end in `-it` / `-fr`, so they stay unique; keep that when you add an `id` there.
- **Menus, buttons, forms and messages**, and the text of the sign-in, home, Contact us, To do's
  and Publications pages, are in `assets/js/i18n.js`: each English phrase with its Italian and
  French version side by side. If you change an English phrase on one of those pages, change the
  same phrase in `i18n.js`, otherwise the page shows English for it.
- **Home page highlights and banner** come from the admin page, which has Italian and French
  fields; empty ones show the English text.
- The observation schedule site shows the English block of the Telescope, EKARUS and Team pages.
