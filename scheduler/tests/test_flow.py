"""End-to-end checks with Flask's test client. No network server is started.

Run:  python -m unittest discover -s tests -v
"""
import email
import glob
import os
import re
import shutil
import tempfile
import unittest
from datetime import date, timedelta

from scheduler import create_app

ADMIN = "oleksandra.rebrysh@inaf.it"
USER = "observer@example.org"
PW = "correct-horse-battery"


class Flow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.app = create_app({
            "TESTING": True,
            "DATABASE": os.path.join(self.tmp, "t.sqlite3"),
            "SECRET_KEY": "test",
            "ADMIN_EMAILS": ADMIN,
            "BASE_URL": "https://sched.test",
            "SESSION_COOKIE_SECURE": False,
        })
        self.app.instance_path = self.tmp          # outbox goes to the temp dir

    def tearDown(self):
        shutil.rmtree(self.tmp)

    # ---------- helpers
    def outbox(self):
        msgs = []
        for path in sorted(glob.glob(os.path.join(self.tmp, "outbox", "*.eml"))):
            with open(path, "rb") as f:
                msgs.append(email.message_from_bytes(f.read()))
        return msgs

    def token(self, client, url):
        html = client.get(url).get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def post(self, client, url, data, form_url=None):
        data = dict(data)
        data["csrf_token"] = self.token(client, form_url or url)
        return client.post(url, data=data, follow_redirects=True)

    def register_and_verify(self, mail, name):
        c = self.app.test_client()
        self.post(c, "/account/register", {"name": name, "email": mail, "institute": "INAF",
                                           "password": PW, "password2": PW})
        msg = [m for m in self.outbox() if m["To"] == mail][-1]
        link = re.search(r"https://sched\.test(/account/verify/\S+)", msg.get_payload(decode=True).decode()).group(1)
        c.get(link)
        r = self.post(c, "/account/login", {"email": mail, "password": PW})
        self.assertIn(name, r.get_data(as_text=True))
        return c

    # ---------- tests
    def test_full_cycle(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra")
        user = self.register_and_verify(USER, "Olga Observer")

        # user can't reach admin pages
        self.assertEqual(user.get("/admin/").status_code, 403)

        # admin opens three nights
        d0 = date.today() + timedelta(days=10)
        r = self.post(admin, "/admin/nights", {"action": "add", "start": d0.isoformat(),
                                               "end": (d0 + timedelta(days=2)).isoformat(), "note": "test run"})
        self.assertIn("3 night(s) opened", r.get_data(as_text=True))

        with self.app.app_context():
            from scheduler.db import get_db
            ids = [r["id"] for r in get_db().execute("SELECT id FROM nights ORDER BY date")]

        # calendar is public and shows the open nights
        html = self.app.test_client().get(f"/?y={d0.year}&m={d0.month}").get_data(as_text=True)
        self.assertIn("night-open", html)

        # user submits a proposal for the first two nights
        n_before = len(self.outbox())
        data = {"title": "Binary star imaging", "summary": "Resolve close binaries.",
                "science_case": "Long case.", "mode": "VIS imaging (science camera)",
                "t_name": ["HD 1234", "HD 5678"], "t_ra": ["01:00:00", "02:00:00"],
                "t_dec": ["+45:00:00", "+50:00:00"], "t_mag": ["6.1", "7.2"],
                "nights": [str(ids[0]), str(ids[1])], "min_nights": "1"}
        r = self.post(user, "/proposals/new", data)
        page = r.get_data(as_text=True)
        self.assertIn("EK-", page)
        self.assertIn("Waiting for review", page)
        new_mail = self.outbox()[n_before:]
        self.assertEqual({m["To"] for m in new_mail}, {USER, ADMIN})   # receipt + admin alert

        # admin accepts one of the two nights
        r = self.post(admin, "/admin/proposals/1", {"decision": "accept", "allocate": [str(ids[0])],
                                                    "message": "Welcome!"})
        self.assertIn("accepted; 1 night(s) booked", r.get_data(as_text=True))
        last = self.outbox()[-1]
        self.assertEqual(last["To"], USER)
        self.assertIn("accepted", last["Subject"])
        self.assertIn("Welcome!", last.get_payload(decode=True).decode())

        # the booked night can no longer be requested
        data2 = dict(data, nights=[str(ids[0])], title="Second try")
        r = self.post(user, "/proposals/new", data2)
        self.assertIn("no longer available", r.get_data(as_text=True))

        # user submits again on a free night, then withdraws it
        data3 = dict(data, nights=[str(ids[2])], title="Third")
        self.post(user, "/proposals/new", data3)
        r = self.post(user, "/proposals/2/withdraw", {}, form_url="/proposals/2")
        self.assertIn("withdrawn", r.get_data(as_text=True))
        self.assertIn("withdrawn", self.outbox()[-1]["Subject"])

        # another user can't see someone else's proposal
        other = self.register_and_verify("someone@example.org", "Someone")
        self.assertEqual(other.get("/proposals/1").status_code, 403)

    def test_reject_needs_reason(self):
        admin = self.register_and_verify(ADMIN, "Oleksandra")
        user = self.register_and_verify(USER, "Olga")
        d0 = date.today() + timedelta(days=5)
        self.post(admin, "/admin/nights", {"action": "add", "start": d0.isoformat(), "end": ""})
        self.post(user, "/proposals/new", {"title": "T", "summary": "S", "science_case": "C",
                                           "mode": "Engineering / calibration", "nights": ["1"]})
        r = self.post(admin, "/admin/proposals/1", {"decision": "reject", "message": ""})
        self.assertIn("Add a short reason", r.get_data(as_text=True))
        r = self.post(admin, "/admin/proposals/1", {"decision": "reject", "message": "Weather season."})
        self.assertIn("rejected and the PI notified", r.get_data(as_text=True))
        self.assertIn("not accepted", self.outbox()[-1]["Subject"])

    def test_unverified_cannot_login_and_csrf_enforced(self):
        c = self.app.test_client()
        self.post(c, "/account/register", {"name": "X", "email": USER, "password": PW, "password2": PW})
        r = self.post(c, "/account/login", {"email": USER, "password": PW})
        self.assertIn("Confirm your e-mail first", r.get_data(as_text=True))
        r = c.post("/account/login", data={"email": USER, "password": PW})   # no token
        self.assertEqual(r.status_code, 400)

    def test_password_reset_link_works_once(self):
        self.register_and_verify(USER, "Olga")
        c = self.app.test_client()
        self.post(c, "/account/forgot", {"email": USER})
        link = re.search(r"https://sched\.test(/account/reset/\S+)", self.outbox()[-1].get_payload(decode=True).decode()).group(1)
        new = "another-long-password"
        r = self.post(c, link, {"password": new, "password2": new})
        self.assertIn("Password changed", r.get_data(as_text=True))
        r = c.get(link, follow_redirects=True)
        self.assertIn("already used", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
