"""Who belongs to the EKARUS team (and so may sign in with their e-mail only, no password).

A person is a team member if their address is
  - in ADMIN_EMAILS, or
  - in the server's team list (Admin -> Team members; approving an access request adds it), or
  - in the wiki's sign-in list docs/assets/js/users.js (hashed), read from the published wiki.
"""
import hashlib
import re
import time
import urllib.request

from flask import current_app

from . import mail
from .db import get_db

_cache = {"at": 0.0, "hashes": set()}
CACHE_SECONDS = 300


def _wiki_hashes():
    wiki = current_app.config.get("WIKI_URL", "")
    if not wiki:
        return set()
    if time.time() - _cache["at"] < CACHE_SECONDS:
        return _cache["hashes"]
    try:
        with urllib.request.urlopen(wiki.rstrip("/") + "/assets/js/users.js", timeout=10) as r:
            text = r.read().decode("utf-8", "replace")
        _cache["hashes"] = set(re.findall(r'"([0-9a-f]{64})"', text))
    except Exception:  # wiki unreachable: keep what we had
        current_app.logger.warning("Couldn't read the wiki's users.js; using the cached team list")
    _cache["at"] = time.time()
    return _cache["hashes"]


def is_team(email):
    email = email.strip().lower()
    if not email:
        return False
    if email in mail.admin_addresses():
        return True
    if get_db().execute("SELECT 1 FROM team WHERE email = ?", (email,)).fetchone():
        return True
    return hashlib.sha256(email.encode()).hexdigest() in _wiki_hashes()


def team_name(email):
    row = get_db().execute("SELECT name FROM team WHERE email = ?", (email.lower(),)).fetchone()
    return (row["name"] if row and row["name"] else email.split("@")[0])


def all_members():
    """Everyone who counts as team, once each: [(email or None, name, source)].
    People only in the wiki's users.js are known by hash only, so their e-mail is None."""
    db = get_db()
    seen, out = set(), []
    for email in mail.admin_addresses():
        h = hashlib.sha256(email.encode()).hexdigest()
        seen.add(h)
        out.append((email, team_name(email), "admin"))
    for r in db.execute("SELECT email, name FROM team ORDER BY name COLLATE NOCASE, email"):
        h = hashlib.sha256(r["email"].encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            out.append((r["email"], r["name"] or r["email"].split("@")[0], "team list"))
    for h in sorted(_wiki_hashes() - seen):
        seen.add(h)
        out.append((None, "", "wiki list"))
    return out
