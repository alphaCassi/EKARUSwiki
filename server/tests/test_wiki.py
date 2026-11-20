"""Contact form API and wiki admin pages. GitHub is replaced by an in-memory fake.

Run:  python -m unittest discover -s tests -v
"""
import base64
import json
import re
import unittest

from ekaruswiki import github, wiki_users
from test_flow import ADMIN, PW, USER, Flow

USERS_JS = 'window.EKARUS_USERS = [\n  // "<sha256-hex>",  // note\n];\n'
SITE = {"banner": "Old banner", "highlights": [{"date": "June", "title": "T1", "text": "x", "done": False}]}


class FakeRepo:
    def __init__(self):
        self.files = {wiki_users.PATH: USERS_JS, "docs/data/site.json": json.dumps(SITE)}
        self.commits = []

    def read(self, path):
        return self.files[path], f"sha-{len(self.commits)}"

    def write(self, path, text, sha, message):
        assert sha == f"sha-{len(self.commits)}", "stale sha"
        self.files[path] = text
        self.commits.append(message)


class Wiki(Flow):
    def setUp(self):
        super().setUp()
        self.app.config.update(WIKI_URL="https://alphacassi.github.io/EKARUSwiki/", GITHUB_TOKEN="x")
        self.repo = FakeRepo()
        self._orig = (github.read, github.write)
        github.read, github.write = self.repo.read, self.repo.write

    def tearDown(self):
        github.read, github.write = self._orig
        super().tearDown()

    def send(self, payload, origin="https://alphacassi.github.io"):
        return self.app.test_client().post("/api/contact", json=payload, headers={"Origin": origin})

    def test_contact_is_stored_emailed_and_cors(self):
        r = self.send({"kind": "contact", "name": "Ana", "email": "ana@x.org",
                       "topic": "Broken link", "page": "Logs", "message": "Link 2 is dead"})
        self.assertEqual(r.get_json(), {"ok": True})
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "https://alphacassi.github.io")
        mail = self.outbox()[-1]
        self.assertEqual(mail["To"], ADMIN)
        self.assertEqual(mail["Reply-To"], "ana@x.org")
        self.assertIn("Link 2 is dead", mail.get_payload(decode=True).decode())
        # other sites get no CORS permission
        r = self.send({"kind": "contact", "name": "B", "email": "b@x.org", "message": "m"}, origin="https://evil.example")
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        # preflight
        r = self.app.test_client().options("/api/contact", headers={"Origin": "https://alphacassi.github.io"})
        self.assertEqual(r.status_code, 204)

    def test_validation_spam_trap_and_rate_limit(self):
        self.assertEqual(self.send({"name": "", "email": "a@b.c", "message": "m"}).status_code, 400)
        self.assertEqual(self.send({"name": "A", "email": "nope", "message": "m"}).status_code, 400)
        n = len(self.outbox())
        r = self.send({"name": "Bot", "email": "b@b.b", "message": "spam", "website": "http://spam"})
        self.assertTrue(r.get_json()["ok"])
        self.assertEqual(len(self.outbox()), n)          # trap: nothing sent or stored
        for _ in range(5):
            self.send({"name": "A", "email": "a@b.cd", "message": "m"})
        self.assertEqual(self.send({"name": "A", "email": "a@b.cd", "message": "m"}).status_code, 429)

    def test_access_request_approved_from_admin_page(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra Rebrysh")
        self.send({"kind": "access", "first_name": "mario", "last_name": "rossi", "email": "Mario@x.org"})
        page = admin.get("/admin/messages").get_data(as_text=True)
        self.assertIn("Access request", page)
        r = self.post(admin, "/admin/messages/1", {"action": "approve"})
        self.assertIn("Added to the team", r.get_data(as_text=True))
        self.assertIn("mario@x.org", admin.get("/admin/team").get_data(as_text=True))
        _, entries = wiki_users.parse(self.repo.files[wiki_users.PATH])
        self.assertEqual(entries, [(wiki_users.email_hash("mario@x.org"), "")])
        self.assertNotIn("mario", self.repo.files[wiki_users.PATH].lower())   # address never stored
        self.assertEqual(self.outbox()[-1]["To"], "mario@x.org")

    def test_team_add_remove_and_non_admin_blocked(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra")
        user = self.register_and_verify(USER, "Olga")
        self.assertEqual(user.get("/admin/team").status_code, 403)
        self.post(admin, "/admin/team", {"action": "add", "email": "c@x.org", "first_name": "C", "last_name": "X"})
        self.post(admin, "/admin/team", {"action": "add", "email": "d@x.org", "first_name": "D", "last_name": "Y"})
        r = self.post(admin, "/admin/team", {"action": "remove", "email": "c@x.org"})
        self.assertIn("removed", r.get_data(as_text=True))
        _, entries = wiki_users.parse(self.repo.files[wiki_users.PATH])
        self.assertEqual([h for h, _ in entries], [wiki_users.email_hash("d@x.org")])

    def test_edit_home_content(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra")
        self.assertIn("Old banner", admin.get("/admin/wiki-content").get_data(as_text=True))
        self.post(admin, "/admin/wiki-content", {
            "banner": "Upcoming: next run",
            "h_date": ["Nov 2026", "June", ""], "h_title": ["New item", "", ""],
            "h_text": ["Fresh news", "", ""], "h_done": ["yes", "", ""]})
        site = json.loads(self.repo.files["docs/data/site.json"])
        self.assertEqual(site["banner"], "Upcoming: next run")
        self.assertEqual(site["highlights"], [{"date": "Nov 2026", "title": "New item", "text": "Fresh news", "done": True}])


if __name__ == "__main__":
    unittest.main()


class Structure(Flow):
    def test_admin_overview_and_home(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra")
        user = self.register_and_verify(USER, "Olga")
        page = admin.get("/admin/").get_data(as_text=True)
        self.assertIn("EKARUSwiki admin", page)
        for part in ("Messages", "Team members", "Home page content", "Observer accounts", "Proposals to review", "Open nights"):
            self.assertIn(part, page)
        self.assertEqual(user.get("/admin/").status_code, 403)
        self.assertIn("Observing nights", user.get("/").get_data(as_text=True))
        self.assertEqual(user.get("/schedule/dashboard").status_code, 301)   # old links still work
        self.assertIn("Olga", admin.get("/admin/accounts").get_data(as_text=True))

    def test_existing_database_file_is_kept(self):
        import os, tempfile
        from ekaruswiki import _default_database
        d = tempfile.mkdtemp()
        self.assertTrue(_default_database(d).endswith("ekaruswiki.sqlite3"))
        open(os.path.join(d, "scheduler.sqlite3"), "w").close()
        self.assertTrue(_default_database(d).endswith("scheduler.sqlite3"))


class TeamSignIn(Flow):
    def setUp(self):
        super().setUp()
        self.app.config["WIKI_URL"] = "https://alphacassi.github.io/EKARUSwiki/"
        from ekaruswiki import team
        team._cache.update(at=10**12, hashes=set())        # don't fetch the real wiki in tests

    def api(self, payload):
        return self.app.test_client().post("/api/signin", json=payload,
                                           headers={"Origin": "https://alphacassi.github.io"})

    def add_member(self, email, name=""):
        with self.app.app_context():
            from ekaruswiki.db import get_db, now
            get_db().execute("INSERT INTO team (email, name, added_at) VALUES (?, ?, ?)", (email, name, now()))
            get_db().commit()

    def test_wiki_signin_is_email_only(self):
        r = self.api({"email": "stranger@x.org"})
        self.assertEqual(r.status_code, 403)
        self.add_member("member@x.org", "Mem Ber")
        r = self.api({"email": "Member@x.org"})
        self.assertEqual(r.get_json(), {"ok": True, "name": "Mem Ber", "admin": False})
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "https://alphacassi.github.io")
        self.assertTrue(self.api({"email": ADMIN}).get_json()["admin"])
        self.assertEqual(len(self.outbox()), 0)                 # no e-mails, no links

    def test_admin_pages_need_admin_password(self):
        c = self.app.test_client()
        self.post(c, "/account/team-signin", {"email": ADMIN, "next": ""}, form_url="/account/login")
        r = c.get("/admin/")                                    # e-mail only: not enough for admin
        self.assertEqual(r.status_code, 302)
        self.assertIn("/account/admin-signin", r.headers["Location"])
        r = self.post(c, "/account/admin-signin", {"email": ADMIN, "password": "wrong", "next": "/admin/"},
                      form_url="/account/admin-signin")
        self.assertIn("Wrong e-mail or admin password", r.get_data(as_text=True))
        r = self.post(c, "/account/admin-signin", {"email": ADMIN, "password": "admin-test-pass", "next": "/admin/"},
                      form_url="/account/admin-signin")
        self.assertIn("EKARUSwiki admin", r.get_data(as_text=True))
        self.add_member("member@x.org")                         # the password alone isn't enough
        r = self.post(self.app.test_client(), "/account/admin-signin",
                      {"email": "member@x.org", "password": "admin-test-pass"}, form_url="/account/admin-signin")
        self.assertIn("Wrong e-mail or admin password", r.get_data(as_text=True))

    def test_team_member_signs_in_on_schedule_site_with_email(self):
        self.add_member("member@x.org")
        c = self.app.test_client()
        r = self.post(c, "/account/team-signin", {"email": "member@x.org", "next": "/dashboard"}, form_url="/account/login")
        self.assertIn("Your dashboard", r.get_data(as_text=True))
        self.assertEqual(c.get("/admin/").status_code, 403)
        r = self.post(self.app.test_client(), "/account/team-signin", {"email": "nobody@x.org"}, form_url="/account/login")
        self.assertIn("on the EKARUS team list", r.get_data(as_text=True))

    def test_team_member_cannot_register_with_password(self):
        c = self.app.test_client()
        r = self.post(c, "/account/register", {"name": "O", "email": ADMIN, "password": PW, "password2": PW})
        self.assertIn("just sign in with your e-mail", r.get_data(as_text=True))

    def test_info_page_from_wiki(self):
        from ekaruswiki import wiki_pages
        orig = wiki_pages._fetch
        wiki_pages._fetch = lambda path: ("https://alphacassi.github.io/EKARUSwiki/" + path,
                                          '<main class="main"><h1>Copernico telescope</h1><img src="../assets/img/copernico.webp"></main>')
        try:
            user = self.register_and_verify(USER, "Olga")
            page = user.get("/info/telescope").get_data(as_text=True)
            self.assertIn("Copernico telescope", page)
            self.assertIn('src="https://alphacassi.github.io/EKARUSwiki/assets/img/copernico.webp"', page)
            self.assertEqual(self.app.test_client().get("/info/telescope").status_code, 302)
        finally:
            wiki_pages._fetch = orig


class SignOut(Flow):
    def setUp(self):
        super().setUp()
        self.app.config["WIKI_URL"] = "https://alphacassi.github.io/EKARUSwiki/"
        from ekaruswiki import team
        team._cache.update(at=10**12, hashes=set())

    def test_logout_redirects_team_to_wiki_signout(self):
        c, _ = self.admin_signin(ADMIN)
        token = __import__("re").search(r'name="csrf_token" value="([^"]+)"', c.get("/admin/").get_data(as_text=True)).group(1)
        r = c.post("/account/logout", data={"csrf_token": token})
        self.assertEqual(r.headers["Location"], "https://alphacassi.github.io/EKARUSwiki/index.html?signout=1")
        self.assertIn("/account/admin-signin", c.get("/admin/").headers["Location"])

    def test_observer_logout_stays_on_schedule_site(self):
        user = self.register_and_verify(USER, "Olga")
        token = __import__("re").search(r'name="csrf_token" value="([^"]+)"', user.get("/dashboard").get_data(as_text=True)).group(1)
        r = user.post("/account/logout", data={"csrf_token": token})
        self.assertEqual(r.headers["Location"], "/")

    def test_wiki_sign_out_ends_server_session(self):
        c, _ = self.admin_signin(ADMIN)
        r = c.get("/account/signout?next=https://alphacassi.github.io/EKARUSwiki/index.html")
        self.assertEqual(r.headers["Location"], "https://alphacassi.github.io/EKARUSwiki/index.html")
        self.assertIn("/account/admin-signin", c.get("/admin/").headers["Location"])
        r = c.get("/account/signout?next=https://evil.example/")      # never sent elsewhere
        self.assertEqual(r.headers["Location"], "/")



class EverySiteVisitStartsAtSignIn(Flow):
    def test_all_pages_need_sign_in_and_sessions_end_with_browser(self):
        anon = self.app.test_client()
        for path in ("/", "/dashboard", "/proposals/new", "/info/telescope", "/admin/"):
            r = anon.get(path)
            self.assertEqual(r.status_code, 302, path)
            self.assertIn("/account/", r.headers["Location"], path)
        self.assertEqual(anon.get("/account/login").status_code, 200)
        c = self.app.test_client()
        token = __import__("re").search(r'name="csrf_token" value="([^"]+)"',
                                        c.get("/account/admin-signin").get_data(as_text=True)).group(1)
        r = c.post("/account/admin-signin", data={"csrf_token": token, "email": ADMIN, "password": "admin-test-pass"})
        cookies = [h for h in r.headers.getlist("Set-Cookie") if h.startswith("session=")]
        self.assertTrue(cookies)
        for h in cookies:
            self.assertNotIn("Expires", h)          # browser-session cookie: gone when the browser closes


class BotProtection(Flow):
    def setUp(self):
        super().setUp()
        self.app.config["WIKI_URL"] = "https://alphacassi.github.io/EKARUSwiki/"
        from ekaruswiki import team
        team._cache.update(at=10**12, hashes=set())

    def wiki(self, payload):
        return self.app.test_client().post("/api/signin", json=payload, headers={"Origin": "https://alphacassi.github.io"})

    def test_too_many_signin_attempts_are_blocked(self):
        for i in range(10):
            self.wiki({"email": f"guess{i}@x.org"})
        r = self.wiki({"email": ADMIN})                     # even a real address is blocked now
        self.assertEqual(r.status_code, 429)

    def test_bot_trap(self):
        r = self.wiki({"email": ADMIN, "website": "http://spam.example"})
        self.assertEqual(r.status_code, 403)

    def test_admin_password_guessing_is_limited(self):
        c = self.app.test_client()
        for _ in range(5):
            self.post(c, "/account/admin-signin", {"email": ADMIN, "password": "guess"}, form_url="/account/admin-signin")
        r = self.post(c, "/account/admin-signin", {"email": ADMIN, "password": "admin-test-pass"}, form_url="/account/admin-signin")
        self.assertIn("Too many attempts", r.get_data(as_text=True))

    def test_signin_log_robots_and_headers(self):
        self.wiki({"email": "stranger@x.org"})
        self.wiki({"email": ADMIN})
        admin, _ = self.admin_signin(ADMIN)
        page = admin.get("/admin/signins").get_data(as_text=True)
        self.assertIn("stranger@x.org", page)
        self.assertIn("Not on the team", page)
        self.assertIn("Admin password", page)
        r = self.app.test_client().get("/robots.txt")
        self.assertIn("Disallow: /", r.get_data(as_text=True))
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")


class AdminOnlyWithPassword(Flow):
    def setUp(self):
        super().setUp()
        self.app.config["WIKI_URL"] = "https://alphacassi.github.io/EKARUSwiki/"
        from ekaruswiki import team
        import hashlib
        team._cache.update(at=10**12, hashes={hashlib.sha256(b"wiki.only@x.org").hexdigest(),
                                              hashlib.sha256(ADMIN.encode()).hexdigest()})

    def test_admin_email_without_password_is_not_admin(self):
        c = self.app.test_client()
        self.post(c, "/account/team-signin", {"email": ADMIN, "next": "/"}, form_url="/account/login")
        page = c.get("/").get_data(as_text=True)
        self.assertNotIn('href="/admin/"', page)                     # no Admin link in the top bar
        self.assertIn("/account/admin-signin", c.get("/admin/schedule/").headers["Location"])

    def test_team_count_includes_admins_and_wiki_list(self):
        with self.app.app_context():
            from ekaruswiki.db import get_db, now
            get_db().execute("INSERT INTO team (email, name, added_at) VALUES ('added@x.org', 'Added', ?)", (now(),))
            get_db().commit()
        admin, _ = self.admin_signin(ADMIN)
        page = admin.get("/admin/").get_data(as_text=True)
        # admin + added@x.org + wiki.only (the admin's own hash in the wiki list isn't counted twice)
        self.assertIn('<span class="stat">3</span><strong>Team members</strong>', page)
        members = admin.get("/admin/team").get_data(as_text=True)
        self.assertIn("Hidden (stored as a hash)", members)


class WikiLanguageBlocks(Flow):
    def test_info_page_uses_english_block(self):
        self.app.config["WIKI_URL"] = "https://alphacassi.github.io/EKARUSwiki/"
        from ekaruswiki import wiki_pages
        wiki_pages._cache.clear()
        orig = wiki_pages._fetch
        wiki_pages._fetch = lambda path: ("https://alphacassi.github.io/EKARUSwiki/" + path,
            '<main class="main" id="main"><div data-lang-block="en"><!-- lang:en --><h1>Copernico telescope</h1><!-- /lang:en --></div>'
            '<div data-lang-block="it"><!-- lang:it --><h1>Telescopio Copernico</h1><!-- /lang:it --></div>'
            '<div data-lang-block="fr"><!-- lang:fr --><h1>Télescope Copernico</h1><!-- /lang:fr --></div></main>')
        try:
            user = self.register_and_verify(USER, "Olga")
            page = user.get("/info/telescope").get_data(as_text=True)
            self.assertIn("Copernico telescope", page)
            self.assertNotIn("Telescopio Copernico", page)
            self.assertNotIn("Télescope Copernico", page)
        finally:
            wiki_pages._fetch = orig


class AdminLinkFromEmail(Flow):
    def signin_from_link(self, path, password="admin-test-pass", email=ADMIN):
        c = self.app.test_client()                     # a fresh browser, as when opening an e-mail
        r = c.get(path)
        self.assertIn("/account/admin-signin", r.headers["Location"])
        page = c.get(r.headers["Location"]).get_data(as_text=True)
        token = __import__("re").search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        nxt = __import__("re").search(r'name="next" value="([^"]*)"', page).group(1)
        # submit to the same address the browser is on, query string included
        return c, c.post(r.headers["Location"], data={"csrf_token": token, "email": email,
                                                      "password": password, "next": nxt})

    def test_link_in_access_request_email_works_and_signs_in(self):
        self.app.config["BASE_URL"] = "https://srv.example.net/"          # trailing slash on purpose
        self.app.test_client().post("/api/contact", json={"name": "A", "email": "a@x.org", "message": "hi",
                                                          "topic": "Access request"})
        body = self.outbox()[-1].get_payload(decode=True).decode()
        link = __import__("re").search(r"https://srv\.example\.net(/\S+)", body).group(1)
        self.assertTrue(link.startswith("/admin/messages/"), link)          # no double slash
        c, r = self.signin_from_link(link)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(c.get(r.headers["Location"]).status_code, 200)

    def test_many_correct_signins_are_never_refused(self):
        for _ in range(8):
            c, r = self.signin_from_link("/admin/")
            self.assertEqual(r.status_code, 302)

    def test_wrong_passwords_by_someone_else_dont_block_you(self):
        for _ in range(6):
            self.signin_from_link("/admin/", password="wrong", email="intruder@x.org")
        c, r = self.signin_from_link("/admin/")
        self.assertEqual(r.status_code, 302)

    def test_admin_password_from_env_with_quotes_or_spaces(self):
        from ekaruswiki import _clean_secret
        self.assertEqual(_clean_secret(' "s3cret$pw" '), "s3cret$pw")
        self.assertEqual(_clean_secret("'abc'"), "abc")
        self.assertEqual(_clean_secret("abc  "), "abc")


class AdminSigninAddressBar(Flow):
    def test_empty_email_in_address_bar_does_not_override_typed_email(self):
        c = self.app.test_client()
        url = "/account/admin-signin?next=/admin/messages/1&email="          # as old links had it
        page = c.get(url).get_data(as_text=True)
        token = __import__("re").search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        r = c.post(url, data={"csrf_token": token, "email": ADMIN, "password": "admin-test-pass",
                              "next": "/admin/messages/1"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/admin/messages/1"))


class NamesEverywhere(Flow):
    def test_name_helpers(self):
        from ekaruswiki import names
        self.assertEqual(names.full_name(" oleksandra ", "REBRYSH"), "Oleksandra Rebrysh")
        self.assertEqual(names.full_name("matteo", "d'ambrogio"), "Matteo D'Ambrogio")
        self.assertEqual(names.full_name("Ivan", "Di Antonio"), "Ivan Di Antonio")
        self.assertEqual(names.split_name("Ivan Di Antonio"), ("Ivan", "Di Antonio"))
        self.assertEqual(names.split_name("Taïssir Cedric Heritier"), ("Taïssir Cedric", "Heritier"))
        self.assertEqual(names.from_email("oleksandra.rebrysh@inaf.it"), "Oleksandra Rebrysh")

    def test_access_request_needs_surname(self):
        c = self.app.test_client()
        r = c.post("/api/contact", json={"kind": "access", "first_name": "Lorenzo", "last_name": "", "email": "l@x.org"})
        self.assertEqual(r.status_code, 400)

    def test_admin_add_needs_surname_and_rename_works(self):
        admin, _ = self.admin_signin(ADMIN)
        r = self.post(admin, "/admin/team", {"action": "add", "email": "lorenzo@x.org", "first_name": "Lorenzo", "last_name": ""},
                      form_url="/admin/team")
        self.assertIn("first name and the surname", r.get_data(as_text=True))
        self.post(admin, "/admin/team", {"action": "add", "email": "lorenzo@x.org", "first_name": "lorenzo", "last_name": "merli"},
                  form_url="/admin/team")
        page = admin.get("/admin/team").get_data(as_text=True)
        self.assertIn("Lorenzo Merli", page)
        self.post(admin, "/admin/team", {"action": "rename", "email": ADMIN, "first_name": "Oleksandra", "last_name": "Rebrysh"},
                  form_url="/admin/team")
        self.assertIn("Oleksandra Rebrysh", admin.get("/admin/team").get_data(as_text=True))

    def test_old_names_are_tidied(self):
        with self.app.app_context():
            from ekaruswiki.db import get_db, init_db, now
            db = get_db()
            db.execute("INSERT INTO team (email, name, added_at) VALUES ('luca.cortese@x.org', 'luca.cortese', ?)", (now(),))
            db.execute("INSERT INTO team (email, name, added_at) VALUES ('a@x.org', 'ANNA BIANCHI', ?)", (now(),))
            db.commit()
            init_db()
            got = {r["email"]: r["name"] for r in db.execute("SELECT email, name FROM team")}
        self.assertEqual(got["luca.cortese@x.org"], "Luca Cortese")
        self.assertEqual(got["a@x.org"], "Anna Bianchi")


class AdminPasswordEveryTime(Flow):
    def form(self, c, url="/account/admin-signin"):
        page = c.get(url).get_data(as_text=True)
        token = __import__("re").search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        return page, token

    def test_signin_page_never_skips_and_never_prefills(self):
        c, _ = self.admin_signin(ADMIN)
        self.assertEqual(c.get("/admin/").status_code, 200)
        page, _ = self.form(c, "/account/admin-signin?next=/admin/&email=" + ADMIN)
        self.assertIn('name="password"', page)                      # asks again
        self.assertIn('name="email" type="email" value=""', page)   # empty e-mail
        self.assertEqual(c.get("/admin/").status_code, 302)          # earlier admin access ended

    def test_admin_access_ends_after_idle(self):
        import time
        c, _ = self.admin_signin(ADMIN)
        with c.session_transaction() as s:
            s["admin_ok"] = time.time() - (self.app.config["ADMIN_IDLE_MINUTES"] * 60 + 5)
        self.assertIn("/account/admin-signin", c.get("/admin/").headers["Location"])


class ProposalFilesAndMail(Flow):
    def make_night(self):
        from datetime import date, timedelta
        admin, _ = self.admin_signin(ADMIN)
        d0 = date.today() + timedelta(days=5)
        self.post(admin, "/admin/schedule/nights", {"action": "add", "start": d0.isoformat(), "end": ""},
                  form_url="/admin/schedule/nights")
        return admin

    def submit(self, user, files):
        import io, re
        page = user.get("/proposals/new").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        data = {"csrf_token": token, "title": "Binaries", "science_case": "Resolve close binaries.",
                "mode": "VIS imaging", "nights": "1",
                "attachments": [(io.BytesIO(b), n) for n, b in files]}
        return user.post("/proposals/new", data=data, content_type="multipart/form-data", follow_redirects=True)

    def test_attachments_and_summary_mail(self):
        admin = self.make_night()
        user = self.register_and_verify(USER, "Olga Tester")
        r = self.submit(user, [("chart.pdf", b"%PDF-1.4 test")])
        page = r.get_data(as_text=True)
        self.assertIn("chart.pdf", page)
        link = __import__("re").search(r'href="(/proposals/1/files/\d+)"', page).group(1)
        dl = user.get(link)
        self.assertEqual(dl.data, b"%PDF-1.4 test")
        self.assertIn("attachment", dl.headers["Content-Disposition"])
        self.assertEqual(admin.get(link).status_code, 200)                       # admin can download
        other = self.register_and_verify("other@x.org", "Other Person")
        self.assertEqual(other.get(link).status_code, 403)                       # others can't
        to_user = [m for m in self.outbox() if m["To"] == USER][-1]
        body = to_user.get_payload(decode=True).decode()
        self.assertIn("Resolve close binaries.", body)
        self.assertIn("chart.pdf", body)
        self.assertIn("accepted or rejected", body)

    def test_attachments_optional_and_checked(self):
        self.make_night()
        user = self.register_and_verify(USER, "Olga Tester")
        r = self.submit(user, [("evil.exe", b"MZ")])
        self.assertIn("can&#39;t be attached", r.get_data(as_text=True))
        self.app.config["UPLOAD_MAX_MB"] = 1
        r = self.submit(user, [("big.pdf", b"x" * (1024 * 1024 + 10))])
        self.assertIn("larger than 1 MB", r.get_data(as_text=True))
        r = self.submit(user, [])
        self.assertIn("EK-", r.get_data(as_text=True))                           # no files: fine


class AccessRequestReject(Flow):
    def test_reject_with_optional_reason(self):
        self.app.test_client().post("/api/contact", json={"kind": "access", "first_name": "Ann", "last_name": "Lee",
                                                          "email": "ann@x.org"})
        admin, _ = self.admin_signin(ADMIN)
        page = admin.get("/admin/messages/1").get_data(as_text=True)
        self.assertIn(">Add to the team<", page)
        self.assertNotIn("tell them", page)
        self.assertNotIn("Mark as done", page)
        self.post(admin, "/admin/messages/1", {"action": "reject", "reason": "Only for the EKARUS team."},
                  form_url="/admin/messages/1")
        m = self.outbox()[-1]
        self.assertEqual(m["To"], "ann@x.org")
        self.assertIn("Only for the EKARUS team.", m.get_payload(decode=True).decode())
        self.assertIn("Rejected", admin.get("/admin/messages?show=all").get_data(as_text=True))


class ForgotPassword(Flow):
    def ask(self, email):
        c = self.app.test_client()
        self.post(c, "/account/forgot", {"email": email}, form_url="/account/forgot")

    def test_reset_end_to_end_from_email(self):
        self.register_and_verify(USER, "Olga Tester")
        self.ask(USER.upper())
        body = [m for m in self.outbox() if m["To"] == USER][-1].get_payload(decode=True).decode()
        link = __import__("re").search(r"https?://[^/\s]+(/account/reset/\S+)", body).group(1)
        c = self.app.test_client()
        r = self.post(c, link, {"password": "a-new-password", "password2": "a-new-password"}, form_url=link)
        self.assertIn("Password changed", r.get_data(as_text=True))
        r = self.post(c, "/account/login", {"email": USER, "password": "a-new-password"}, form_url="/account/login")
        self.assertIn("Sign out", r.get_data(as_text=True))
        r = self.app.test_client().get(link, follow_redirects=True)
        self.assertIn("already used", r.get_data(as_text=True))

    def test_team_member_without_password_gets_no_reset(self):
        n = len(self.outbox())
        c = self.app.test_client()
        self.post(c, "/account/team-signin", {"email": ADMIN}, form_url="/account/login")
        self.ask(ADMIN)
        self.assertEqual(len(self.outbox()), n)


class CodeFoldersAndBookedNights(Flow):
    def setup_booked(self):
        import io, re
        from datetime import date, timedelta
        admin, _ = self.admin_signin(ADMIN)
        d0 = date.today() + timedelta(days=5)
        self.post(admin, "/admin/schedule/nights", {"action": "add", "start": d0.isoformat(), "end": ""},
                  form_url="/admin/schedule/nights")
        user = self.register_and_verify(USER, "Olga Tester")
        page = user.get("/proposals/new").get_data(as_text=True)
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        user.post("/proposals/new", content_type="multipart/form-data", data={
            "csrf_token": token, "title": "Binary stars", "science_case": "Secret case", "mode": "VIS imaging",
            "nights": "1", "attachments": [(io.BytesIO(b"%PDF"), "chart.pdf")]})
        self.post(admin, "/admin/schedule/proposals/1", {"decision": "accept", "allocate": ["1"]},
                  form_url="/admin/schedule/proposals/1")
        return admin, user, d0

    def test_folder_named_by_code_and_private(self):
        import os
        admin, user, _ = self.setup_booked()
        with self.app.app_context():
            from ekaruswiki.db import get_db
            code = get_db().execute("SELECT code FROM proposals WHERE id = 1").fetchone()["code"]
        folder = os.path.join(self.app.instance_path, "uploads", code)
        self.assertTrue(os.path.isdir(folder))
        self.assertEqual(len(os.listdir(folder)), 1)
        other = self.register_and_verify("other@x.org", "Other Person")
        self.assertEqual(other.get("/proposals/1").status_code, 403)
        self.assertEqual(other.get("/proposals/1/files/1").status_code, 403)

    def test_booked_night_shows_title_and_pi_to_everyone_but_nothing_else(self):
        admin, user, d0 = self.setup_booked()
        other = self.register_and_verify("other@x.org", "Other Person")
        n = [x for x in other.get(f"/calendar.json?y={d0.year}&m={d0.month}").get_json()["nights"] if x["status"] == "booked"][0]
        self.assertEqual(n["title"], "Binary stars")
        self.assertEqual(n["pi"], "Olga Tester")
        self.assertTrue(n["code"].startswith("EK-"))
        self.assertEqual(n["link"], "")                          # no link to someone else's proposal
        self.assertNotIn("Secret case", str(n))
        mine = [x for x in user.get(f"/calendar.json?y={d0.year}&m={d0.month}").get_json()["nights"] if x["status"] == "booked"][0]
        self.assertTrue(mine["mine"] and mine["link"].endswith("/proposals/1"))

    def test_old_numbered_folder_is_renamed(self):
        import os
        admin, user, _ = self.setup_booked()
        base = os.path.join(self.app.instance_path, "uploads")
        with self.app.app_context():
            from ekaruswiki.db import get_db, init_db
            code = get_db().execute("SELECT code FROM proposals WHERE id = 1").fetchone()["code"]
            os.rename(os.path.join(base, code), os.path.join(base, "1"))
            init_db()
        self.assertTrue(os.path.isdir(os.path.join(base, code)))
        self.assertFalse(os.path.exists(os.path.join(base, "1")))
        self.assertEqual(user.get("/proposals/1/files/1").status_code, 200)


class FileRetention(CodeFoldersAndBookedNights):
    def test_files_deleted_after_retention(self):
        import os
        from datetime import date, timedelta
        admin, user, d0 = self.setup_booked()
        with self.app.app_context():
            from ekaruswiki.db import get_db
            from ekaruswiki.schedule import files
            db = get_db()
            code = db.execute("SELECT code FROM proposals WHERE id = 1").fetchone()["code"]
            self.assertEqual(files.delete_expired(force=True), 0)          # night still ahead: kept
            past = (date.today() - timedelta(days=self.app.config["RETENTION_DAYS"] + 1)).isoformat()
            db.execute("UPDATE nights SET date = ?", (past,))
            db.commit()
            self.assertEqual(files.delete_expired(force=True), 1)
        self.assertFalse(os.path.exists(os.path.join(self.app.instance_path, "uploads", code)))
        self.assertEqual(user.get("/proposals/1/files/1").status_code, 404)
        self.assertIn("Binary stars", user.get("/proposals/1").get_data(as_text=True))   # proposal itself stays
