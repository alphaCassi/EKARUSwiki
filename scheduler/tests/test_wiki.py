"""Contact form API and wiki admin pages. GitHub is replaced by an in-memory fake.

Run:  python -m unittest discover -s tests -v
"""
import json
import unittest

from scheduler import github, wiki_users
from test_flow import ADMIN, USER, Flow

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
        self.assertIn("Registered on the wiki", r.get_data(as_text=True))
        _, entries = wiki_users.parse(self.repo.files[wiki_users.PATH])
        self.assertEqual(entries, [(wiki_users.email_hash("mario@x.org"), "MR")])
        self.assertNotIn("mario", self.repo.files[wiki_users.PATH].lower())   # address never stored
        self.assertEqual(self.outbox()[-1]["To"], "mario@x.org")

    def test_wiki_users_add_remove_and_non_admin_blocked(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra")
        user = self.register_and_verify(USER, "Olga")
        self.assertEqual(user.get("/admin/wiki-users").status_code, 403)
        self.post(admin, "/admin/wiki-users", {"action": "add", "email": "c@x.org", "note": "CX"})
        self.post(admin, "/admin/wiki-users", {"action": "add", "email": "d@x.org", "note": ""})
        r = self.post(admin, "/admin/wiki-users", {"action": "remove", "email": "c@x.org"})
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
