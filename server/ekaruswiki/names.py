"""People's names, stored the same way everywhere: "First Surname".

Forms ask for the first name and the surname separately; full_name() joins them.
"""
import re

# Lower-case words that start many surnames (Di Antonio, D'Ambrogio, van Gaalen ...)
PARTICLES = {"di", "de", "da", "del", "della", "dei", "degli", "des", "du", "la", "le", "van", "von", "der", "den"}


def _cap_word(w):
    """Capitalise a word the user typed all in lower or upper case; keep mixed case (McDonald)."""
    if not w or not (w.islower() or w.isupper()):
        return w
    return "-".join("'".join(x[:1].upper() + x[1:].lower() for x in part.split("'")) for part in w.split("-"))


def clean(text):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return " ".join(_cap_word(w) for w in text.split(" ")) if text else ""


def full_name(first, last):
    return " ".join(p for p in (clean(first), clean(last)) if p)[:120]


def split_name(full):
    """Best guess of (first, surname) from a stored full name, to pre-fill an edit form."""
    words = clean(full).split(" ")
    if len(words) < 2:
        return (words[0] if words and words[0] else ""), ""
    i = len(words) - 1
    while i > 1 and words[i - 1].lower() in PARTICLES:
        i -= 1
    return " ".join(words[:i]), " ".join(words[i:])


def from_email(email):
    """A readable name from an address like oleksandra.rebrysh@inaf.it, when nothing better is known."""
    local = (email or "").split("@")[0]
    parts = [p for p in re.split(r"[._\-+]+", local) if p and not p.isdigit()]
    return clean(" ".join(parts)) or local


def has_surname(full):
    return len(clean(full).split(" ")) >= 2
