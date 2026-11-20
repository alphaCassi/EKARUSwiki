"""Files attached to proposals: checked, then stored in a folder named after the proposal code,
instance/uploads/<code>/ (e.g. EK-2026-001), created when the proposal is submitted.
Only the proposer and admins can download them."""
import os
import secrets

from flask import current_app
from werkzeug.utils import secure_filename

from ..db import get_db, now

ALLOWED = {"pdf", "png", "jpg", "jpeg", "gif", "webp", "txt", "csv", "fits", "fit", "fz",
           "doc", "docx", "odt", "xls", "xlsx", "ods", "ppt", "pptx", "odp", "zip"}


def limits():
    cfg = current_app.config
    return cfg["UPLOAD_MAX_FILES"], cfg["UPLOAD_MAX_MB"]


def check(files):
    """files: list of werkzeug FileStorage. Returns (ok_files, errors)."""
    max_files, max_mb = limits()
    files = [f for f in files if f and f.filename]
    errors = []
    if len(files) > max_files:
        errors.append(f"Attach at most {max_files} files.")
    for f in files:
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED:
            errors.append(f"{f.filename}: this type of file can't be attached "
                          f"(allowed: {', '.join(sorted(ALLOWED))}).")
            continue
        f.stream.seek(0, os.SEEK_END)
        size = f.stream.tell()
        f.stream.seek(0)
        if size > max_mb * 1024 * 1024:
            errors.append(f"{f.filename} is larger than {max_mb} MB.")
    return files, errors


def folder(pid):
    row = get_db().execute("SELECT code FROM proposals WHERE id = ?", (pid,)).fetchone()
    name = secure_filename(row["code"]) if row else ""
    return os.path.join(current_app.instance_path, "uploads", name or str(int(pid)))


def rename_old_folders():
    """Folders made by the previous version were named by number (uploads/1/): rename them by code."""
    base = os.path.join(current_app.instance_path, "uploads")
    if not os.path.isdir(base):
        return
    for r in get_db().execute("SELECT id, code FROM proposals"):
        old, new = os.path.join(base, str(r["id"])), os.path.join(base, secure_filename(r["code"]))
        if os.path.isdir(old) and not os.path.exists(new):
            os.rename(old, new)


def save(pid, files):
    os.makedirs(folder(pid), exist_ok=True)
    db = get_db()
    for f in files:
        name = secure_filename(f.filename) or "file"
        stored = secrets.token_hex(12) + "-" + name
        path = os.path.join(folder(pid), stored)
        f.save(path)
        db.execute("INSERT INTO proposal_files (proposal_id, filename, stored, size, uploaded_at)"
                   " VALUES (?, ?, ?, ?, ?)", (pid, f.filename[:200], stored, os.path.getsize(path), now()))


def list_for(pid):
    return get_db().execute("SELECT * FROM proposal_files WHERE proposal_id = ? ORDER BY id", (pid,)).fetchall()


def expiry_date(pid):
    """Files are kept until RETENTION_DAYS after the proposal's last observing night
    (the last allocated night, or the last requested one if none was allocated)."""
    from datetime import date, timedelta
    db = get_db()
    last = db.execute("SELECT MAX(date) FROM nights WHERE proposal_id = ?", (pid,)).fetchone()[0] or \
        db.execute("SELECT MAX(n.date) FROM proposal_nights pn JOIN nights n ON n.id = pn.night_id"
                   " WHERE pn.proposal_id = ?", (pid,)).fetchone()[0]
    if not last:
        return None
    return date.fromisoformat(last) + timedelta(days=current_app.config["RETENTION_DAYS"])


_last_cleanup = {"at": 0.0}


def delete_expired(force=False):
    """Delete the folders and files of proposals whose retention period is over.
    Runs at most once an hour (on requests to the server), and at start-up."""
    import shutil
    import time
    from datetime import date
    if not force and time.time() - _last_cleanup["at"] < 3600:
        return 0
    _last_cleanup["at"] = time.time()
    db = get_db()
    removed = 0
    for r in db.execute("SELECT DISTINCT proposal_id FROM proposal_files").fetchall():
        pid = r["proposal_id"]
        until = expiry_date(pid)
        if until and date.today() > until:
            shutil.rmtree(folder(pid), ignore_errors=True)
            db.execute("DELETE FROM proposal_files WHERE proposal_id = ?", (pid,))
            removed += 1
    # empty folders of proposals past their date
    base = os.path.join(current_app.instance_path, "uploads")
    if os.path.isdir(base):
        for p in db.execute("SELECT id, code FROM proposals").fetchall():
            d = os.path.join(base, secure_filename(p["code"]))
            until = expiry_date(p["id"])
            if os.path.isdir(d) and until and date.today() > until:
                shutil.rmtree(d, ignore_errors=True)
    db.commit()
    return removed
