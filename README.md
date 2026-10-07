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
- **Observation Schedule** button opens the scheduler app in a new tab; set its address in `schedulerUrl` (`assets/js/config.js`). Until then it shows `pages/observation-schedule.html`.
- **DAO-EKARUS** button links straight to the DAO server; `pages/dao-ekarus.html` is kept but not linked.
- **Team photos** (`pages/team.html`): save each photo as `assets/img/team/<first-last>.webp` (about 300 px wide) and replace that person's `<span class="photo" ...></span>` with `<img class="photo" src="../assets/img/team/<first-last>.webp" width="300" height="360" alt="">`. The members table is below the diagram.
- **Partner logos**: the `<footer class="partners">` block at the bottom of every page.
- **"Happening" banner**: the `<p class="happening">` line in each page's header.
- **Highlights**: add a new `<li>` at the top of the list in `home.html`.
- **Bench subsystems** (`pages/bench.html`): each subsystem is a
  `<section class="subsystem-panel" id="...">` with a matching
  `<button data-target="...">`. Panels can be linked directly, e.g.
  `pages/bench.html#wfs-channel`.
- **Images**: put them in `assets/img/` (WebP or JPEG, ideally under ~200 KB) and always
  set `width`, `height` and `alt`.

## To-do list

The spreadsheet lives in the repository at `templates/EKARUS_todo.xlsx`. The To-do page links to it
once `githubRepo` (e.g. `"owner/ekarus"`) is set in `assets/js/config.js`.

The rows shown on the page are written in `pages/todo.html`. Editing the spreadsheet does not change
the page by itself: update the table in `todo.html` too. (Optional: if the list is moved to a Google
Sheet published as CSV, set `todoSheetUrl` and the page reads it automatically.)

## Publishing on GitHub Pages

1. This folder is `docs/` in the EKARUS repository; push the repository to the `main` branch.
2. Repository **Settings → Pages → Build and deployment**: Source "Deploy from a branch",
   branch `main`, folder **`/docs`** (so only the wiki is published, not the scheduler code).
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
