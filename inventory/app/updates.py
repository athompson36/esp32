"""Check for firmware/OS updates via GitHub releases."""
import json
import os
import urllib.error
import urllib.request

from config import REPO_ROOT, FIRMWARE_REPOS_FOR_UPDATES

GITHUB_API_LATEST = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
GITHUB_API_TAG = "https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
TIMEOUT = 10


def fetch_release_with_assets(owner: str, repo: str, tag: str = None):
    """Fetch a release (latest or by tag) with assets. Returns { tag, name, url, assets: [{ name, browser_download_url, size }], error? }."""
    if tag:
        url = GITHUB_API_TAG.format(owner=owner, repo=repo, tag=tag)
    else:
        url = GITHUB_API_LATEST.format(owner=owner, repo=repo)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            assets = [
                {"name": a.get("name", ""), "browser_download_url": a.get("browser_download_url", ""), "size": a.get("size", 0)}
                for a in data.get("assets", [])
            ]
            return {
                "tag": data.get("tag_name", ""),
                "name": data.get("name") or data.get("tag_name", ""),
                "url": data.get("html_url", ""),
                "published": data.get("published_at", ""),
                "assets": assets,
                "error": None,
            }
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return {"error": str(e), "tag": "", "url": "", "assets": []}


def fetch_latest_release(owner: str, repo: str):
    url = GITHUB_API_LATEST.format(owner=owner, repo=repo)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            return {
                "tag": data.get("tag_name", ""),
                "name": data.get("name") or data.get("tag_name", ""),
                "url": data.get("html_url", ""),
                "published": data.get("published_at", ""),
            }
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return {"error": str(e), "tag": "", "url": ""}


def get_updates():
    """Return list of { name, device, tag, url, error? } for each configured repo."""
    results = []
    for entry in FIRMWARE_REPOS_FOR_UPDATES:
        owner = entry["owner"]
        repo = entry["repo"]
        name = entry.get("name", repo)
        device = entry.get("device", "")
        info = fetch_latest_release(owner, repo)
        results.append({
            "name": name,
            "device": device,
            "repo": f"{owner}/{repo}",
            "tag": info.get("tag", ""),
            "release_name": info.get("name", ""),
            "url": info.get("url", ""),
            "published": info.get("published", ""),
            "error": info.get("error"),
        })
    return results
