"""Read and write files of the wiki repository through the GitHub REST API.

Every change made from the admin pages becomes a normal commit on the repository,
so GitHub Pages republishes the wiki and the history shows who changed what.
"""
import base64
import json
import urllib.error
import urllib.request

from flask import current_app

API = "https://api.github.com"


class GitHubError(Exception):
    pass


def configured():
    return bool(current_app.config["GITHUB_TOKEN"] and current_app.config["GITHUB_REPO"])


def _request(method, path, body=None):
    cfg = current_app.config
    req = urllib.request.Request(
        f"{API}/repos/{cfg['GITHUB_REPO']}/contents/{path}"
        + (f"?ref={cfg['GITHUB_BRANCH']}" if method == "GET" else ""),
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {cfg['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ekaruswiki-server",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise GitHubError(f"GitHub answered {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise GitHubError(f"GitHub can't be reached: {e.reason}") from None


def read(path):
    """Return (text, sha) of a file in the repository."""
    if not configured():
        raise GitHubError("GITHUB_TOKEN is not set, so the wiki can't be changed from here.")
    data = _request("GET", path)
    return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]


def write(path, text, sha, message):
    """Commit new content for a file. sha must be the one returned by read()."""
    if not configured():
        raise GitHubError("GITHUB_TOKEN is not set, so the wiki can't be changed from here.")
    _request("PUT", path, {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode(),
        "sha": sha,
        "branch": current_app.config["GITHUB_BRANCH"],
    })
