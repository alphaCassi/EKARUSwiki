"""The wiki's sign-in list (docs/assets/js/users.js): SHA-256 hashes of e-mail addresses.

Same format as docs/tools/manage_users.py, so both can be used on the same file.
"""
import hashlib
import re

PATH = "docs/assets/js/users.js"
ENTRY = re.compile(r'^\s*"([0-9a-f]{64})",?\s*(?://\s*(.*))?$')
LIST_START = "window.EKARUS_USERS = ["
LIST_END = "];"


def email_hash(email):
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def parse(text):
    start = text.index(LIST_START) + len(LIST_START)
    end = text.index(LIST_END, start)
    entries = []
    for line in text[start:end].splitlines():
        m = ENTRY.match(line)
        if m:
            entries.append((m.group(1), (m.group(2) or "").strip()))
    return text[:start], entries


def serialize(header, entries):
    lines = ['  // "<sha256-hex>",  // <optional note, e.g. initials>']
    for h, note in entries:
        lines.append(f'  "{h}",' + (f"  // {note}" if note else ""))
    return header + "\n" + "\n".join(lines) + "\n" + LIST_END + "\n"
