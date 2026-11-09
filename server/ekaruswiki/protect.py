"""Protection against bots and guessing.

- Limits: each connection (IP address, stored only as a short hash) gets a limited number of
  attempts per kind of form within a time window.
- Bot trap: forms carry a hidden "website" field that people never see; bots fill it in.
- Sign-in log: every sign-in attempt, for the admin page "Sign-ins".
"""
import hashlib
import time

from flask import request

from .db import get_db, now

# kind: (max attempts, window in seconds)
LIMITS = {
    "signin": (10, 10 * 60),        # e-mail sign-in (wiki and server)
    "admin": (5, 15 * 60),          # admin password
    "login": (10, 15 * 60),         # observer password
    "register": (5, 60 * 60),
    "forgot": (5, 60 * 60),
}


def ip_hash():
    return hashlib.sha256((request.remote_addr or "").encode()).hexdigest()[:16]


def too_many(kind):
    """Count this attempt; True if the connection went over the limit for this kind."""
    limit, window = LIMITS[kind]
    db = get_db()
    t = time.time()
    db.execute("DELETE FROM attempts WHERE at < ?", (t - 24 * 3600,))          # keep the table small
    n = db.execute("SELECT COUNT(*) FROM attempts WHERE kind = ? AND ip_hash = ? AND at >= ?",
                   (kind, ip_hash(), t - window)).fetchone()[0]
    db.execute("INSERT INTO attempts (kind, ip_hash, at) VALUES (?, ?, ?)", (kind, ip_hash(), t))
    db.commit()
    return n >= limit


def is_bot(form_value):
    """The hidden 'website' field was filled in: only bots do that."""
    return bool((form_value or "").strip())


def log_signin(email, source, ok, reason=""):
    db = get_db()
    db.execute("INSERT INTO signin_log (at, email, source, ok, reason, ip_hash) VALUES (?, ?, ?, ?, ?, ?)",
               (now(), (email or "")[:200], source, int(ok), reason, ip_hash()))
    db.execute("DELETE FROM signin_log WHERE id NOT IN (SELECT id FROM signin_log ORDER BY id DESC LIMIT 2000)")
    db.commit()
