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
        self.send({"kind": "access", "name": "Mario Rossi", "email": "Mario@x.org"})
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
        self.post(admin, "/admin/team", {"action": "add", "email": "c@x.org", "name": "C X"})
        self.post(admin, "/admin/team", {"action": "add", "email": "d@x.org", "name": ""})
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


class AdminRemembered(Flow):
    def test_admin_signin_page_skipped_when_remembered(self):
        c, _ = self.admin_signin(ADMIN)
        r = c.get("/account/admin-signin?next=%2Fadmin%2F&email=" + ADMIN)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/admin/"))


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
