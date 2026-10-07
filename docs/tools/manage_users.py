#!/usr/bin/env python3
"""Register, remove or list EKARUS wiki users.

Users are stored in assets/js/users.js as SHA-256 hashes of their lower-case
e-mail address, so the addresses are not written in the repository.

Usage (run from anywhere; Python 3.6+, no extra packages):
    python tools/manage_users.py add someone@inaf.it [--note "initials or role"]
    python tools/manage_users.py remove someone@inaf.it
    python tools/manage_users.py check someone@inaf.it
    python tools/manage_users.py list

After add/remove: commit and push assets/js/users.js. GitHub Pages republishes
within a minute or two.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

USERS_FILE = Path(__file__).resolve().parent.parent / "assets" / "js" / "users.js"
ENTRY = re.compile(r'^\s*"([0-9a-f]{64})",?\s*(?://\s*(.*))?$')
LIST_START = "window.EKARUS_USERS = ["
LIST_END = "];"


def email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def read():
    text = USERS_FILE.read_text(encoding="utf-8")
    start = text.index(LIST_START) + len(LIST_START)
    end = text.index(LIST_END, start)
    header, body = text[:start], text[start:end]
    entries = []
    for line in body.splitlines():
        m = ENTRY.match(line)
        if m:
            entries.append((m.group(1), (m.group(2) or "").strip()))
    return header, entries


def write(header, entries):
    lines = ['  // "<sha256-hex>",  // <optional note, e.g. initials>']
    for h, note in entries:
        lines.append(f'  "{h}",' + (f"  // {note}" if note else ""))
    USERS_FILE.write_text(header + "\n" + "\n".join(lines) + "\n" + LIST_END + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="register an e-mail address")
    a.add_argument("email")
    a.add_argument("--note", default="", help="short label kept next to the hash (avoid writing the e-mail)")
    for name, text in (("remove", "unregister an e-mail address"), ("check", "is this address registered?")):
        sub.add_parser(name, help=text).add_argument("email")
    sub.add_parser("list", help="show registered hashes and notes")
    args = p.parse_args()

    header, entries = read()
    hashes = [h for h, _ in entries]

    if args.cmd == "list":
        print(f"{len(entries)} registered user(s)")
        for h, note in entries:
            print(f"  {h[:12]}…  {note}")
        return 0

    if "@" not in args.email:
        print("That doesn't look like an e-mail address.", file=sys.stderr)
        return 1
    h = email_hash(args.email)

    if args.cmd == "check":
        print("registered" if h in hashes else "not registered")
        return 0 if h in hashes else 1

    if args.cmd == "add":
        if h in hashes:
            print("Already registered; nothing changed.")
            return 0
        if "@" in args.note:
            print("Leave the e-mail out of --note; it would be published.", file=sys.stderr)
            return 1
        entries.append((h, args.note.replace("\n", " ")))
        write(header, entries)
        print(f"Added. Now commit and push {USERS_FILE.relative_to(USERS_FILE.parents[2])}.")
        return 0

    if args.cmd == "remove":
        if h not in hashes:
            print("Not registered; nothing changed.")
            return 1
        write(header, [(x, n) for x, n in entries if x != h])
        print(f"Removed. Now commit and push {USERS_FILE.relative_to(USERS_FILE.parents[2])}.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
