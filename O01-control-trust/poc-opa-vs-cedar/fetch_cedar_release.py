#!/usr/bin/env python3
from __future__ import annotations
import json
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent
headers = {"Accept": "application/vnd.github+json", "User-Agent": "helixar-o01-poc"}
payload = None
for page in range(1, 8):
    url = f"https://api.github.com/repos/cedar-policy/cedar/releases?per_page=100&page={page}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        releases = json.load(response)
    for release in releases:
        tag = release["tag_name"]
        if tag.startswith("cedar-policy-cli-v"):
            payload = release
            break
    if payload is not None or not releases:
        break
if payload is None:
    raise SystemExit("No cedar-policy-cli release found")
(root / "cedar-release.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "tag": payload["tag_name"],
    "target_commitish": payload["target_commitish"],
    "published_at": payload["published_at"],
    "assets": [{"name": a["name"], "url": a["browser_download_url"], "size": a["size"], "digest": a.get("digest")} for a in payload["assets"]],
}, indent=2))
