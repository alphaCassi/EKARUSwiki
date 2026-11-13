"""Protection against bots and guessing.

- Limits: failed sign-in attempts are counted per connection and e-mail (stored only as a short
  hash) within a time window; a successful sign-in clears them. Registration and password reset
  count every use.
- Bot trap: forms carry a hidden "website" field that people never see; bots fill it in.
- Sign-in log: every sign-in attempt, for the admin page "Sign-ins".
"""
import hashlib
import time

from flask import request

from .db import get_db, now

# kind: (max attempts, window in seconds)
LIMITS = {
    "signin": (10, 10 * 60),        # unknown e-mails tried (wiki and server sign-in)
    "admin": (5, 15 * 60),          # wrong admin passwords
    "login": (10, 15 * 60),         # wrong observer passwords
    "register": (5, 60 * 60),
    "forgot": (5, 60 * 60),
}


def ip_hash():
    return hashlib.sha256((request.remote_addr or "").encode()).hexdigest()[:16]


def _key(who=""):
    """Connection, plus the e-mail tried when there is one, so one person's mistakes
    don't block someone else behind the same proxy."""
    return hashlib.sha256(f"{request.remote_addr or ''}|{(who or '').strip().lower()}".encode()).hexdigest()[:16]


def blocked(kind, who=""):
    """True if this connection (and e-mail) has used up its failed attempts for this kind."""
    limit, window = LIMITS[kind]
    db = get_db()
    t = time.time()
    db.execute("DELETE FROM attempts WHERE at < ?", (t - 24 * 3600,))          # keep the table small
    db.commit()
    n = db.execute("SELECT COUNT(*) FROM attempts WHERE kind = ? AND ip_hash = ? AND at >= ?",
                   (kind, _key(who), t - window)).fetchone()[0]
    return n >= limit


def failed(kind, who=""):
    """Count one failed attempt (wrong password, unknown address)."""
    db = get_db()
    db.execute("INSERT INTO attempts (kind, ip_hash, at) VALUES (?, ?, ?)", (kind, _key(who), time.time()))
    db.commit()


def succeeded(kind, who=""):
    """A successful sign-in clears the earlier failed attempts."""
    db = get_db()
    db.execute("DELETE FROM attempts WHERE kind = ? AND ip_hash = ?", (kind, _key(who)))
    db.commit()


def too_many(kind):
    """For forms where every use counts (registration, password reset): count it and check."""
    over = blocked(kind)
    failed(kind)
    return over


def is_bot(form_value):
    """The hidden 'website' field was filled in: only bots do that."""
    return bool((form_value or "").strip())


def log_signin(email, source, ok, reason=""):
    db = get_db()
    db.execute("INSERT INTO signin_log (at, email, source, ok, reason, ip_hash) VALUES (?, ?, ?, ?, ?, ?)",
               (now(), (email or "")[:200], source, int(ok), reason, ip_hash()))
    db.execute("DELETE FROM signin_log WHERE id NOT IN (SELECT id FROM signin_log ORDER BY id DESC LIMIT 2000)")
    db.commit()
