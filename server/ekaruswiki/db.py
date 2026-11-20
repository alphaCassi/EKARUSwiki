"""SQLite helpers. One connection per request, closed automatically."""
import sqlite3
from datetime import datetime, timezone

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    with current_app.open_resource("schema.sql") as f:
        conn.executescript(f.read().decode("utf-8"))
    # Columns added after the first release: add them to existing databases.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
    for col, decl in (("magic_nonce", "TEXT NOT NULL DEFAULT ''"), ("magic_sent_at", "TEXT NOT NULL DEFAULT ''")):
        if col not in cols:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {decl}")
    mcols = {r["name"] for r in conn.execute("PRAGMA table_info(messages)")}
    if "outcome" not in mcols:                       # access requests: approved / rejected
        conn.execute("ALTER TABLE messages ADD COLUMN outcome TEXT NOT NULL DEFAULT ''")
    _tidy_names(conn)
    from .schedule.files import rename_old_folders
    rename_old_folders()
    from .schedule.files import delete_expired
    delete_expired(force=True)
    conn.commit()


def _tidy_names(conn):
    """Names stored by earlier versions: "oleksandra.rebrysh" or "" become "Oleksandra Rebrysh",
    all-lower or all-upper names get capitals. A name without a surname is left for the admin
    to complete on the Team members page."""
    from .names import clean, from_email
    for table in ("team", "users"):
        for r in conn.execute(f"SELECT email, name FROM {table}").fetchall():
            local = r["email"].split("@")[0].lower()
            name = r["name"] or ""
            new = from_email(r["email"]) if (not name.strip() or name.strip().lower() == local) else clean(name)
            if new != name:
                conn.execute(f"UPDATE {table} SET name = ? WHERE email = ?", (new, r["email"]))


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@click.command("init-db")
def init_db_command():
    """Create the tables (safe to run again: existing data is kept)."""
    init_db()
    click.echo("Database ready.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    with app.app_context():
        init_db()
