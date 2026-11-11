"""Selected wiki pages shown to observers on the schedule site.

The content is read from the published wiki (WIKI_URL), so it's written only once, in docs/.
Only the main part of each page is used; links to images and other pages are made absolute.
"""
import re
import time
import urllib.request
from urllib.parse import urljoin

from flask import current_app
from markupsafe import Markup

# key: (wiki file, title)
PAGES = {
    "telescope": ("pages/telescope.html", "Telescope"),
    "bench": ("pages/bench.html", "EKARUS"),
    "team": ("pages/team.html", "Team and contacts"),
}
CACHE_SECONDS = 600
_cache = {}


def _fetch(path):
    base = current_app.config.get("WIKI_URL", "").rstrip("/") + "/"
    url = urljoin(base, path)
    with urllib.request.urlopen(url, timeout=10) as r:
        return url, r.read().decode("utf-8", "replace")


def _main_part(html):
    m = re.search(r'<main[^>]*>(.*?)</main>', html, re.S)
    return m.group(1) if m else ""


def _absolute(html, page_url):
    def fix(m):
        attr, quote, value = m.group(1), m.group(2), m.group(3)
        if value.startswith(("#", "http:", "https:", "mailto:", "data:")):
            return m.group(0)
        return f'{attr}={quote}{urljoin(page_url, value)}{quote}'
    return re.sub(r'\b(src|href)=(["\'])(.*?)\2', fix, html)


def get(page):
    """Return (Markup html, error message)."""
    if not current_app.config.get("WIKI_URL"):
        return None, "WIKI_URL isn't set on the server."
    hit = _cache.get(page)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1], None
    try:
        path = PAGES[page][0]
        url, html = _fetch(path)
        content = _absolute(_main_part(html), url)
        if page == "team":            # add the contact list from the wiki's Contact us page
            curl, chtml = _fetch("pages/contact.html")
            m = re.search(r'(<section[^>]*aria-labelledby="contacts-title".*?</section>)', chtml, re.S)
            if m:
                content += _absolute(m.group(1), curl)
        result = Markup(content)      # our own wiki content, from our own repository
        _cache[page] = (time.time(), result)
        return result, None
    except Exception:
        current_app.logger.exception("Couldn't load wiki page %s", page)
        if hit:
            return hit[1], None
        return None, "The wiki can't be reached right now. Please try again later."
