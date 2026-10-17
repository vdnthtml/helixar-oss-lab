#!/usr/bin/env python3
"""Collect pinned repository and license metadata for all O06 candidates."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
REPOS = {
    "Activepieces": "activepieces",
    "Nango": "nango",
    "Twenty": "twenty",
    "Apache Unomi": "unomi",
    "OpenFGA": "openfga",
    "Klaro": "klaro",
    "dedupe": "dedupe",
    "OpenCATS": "opencats",
    "Frappe HR": "frappe-hr",
}
LICENSE_FILES = {
    "Activepieces": ["LICENSE", "packages/ee/LICENSE"],
    "Nango": ["LICENSE", "LICENSE_SHORT"],
    "Twenty": ["LICENSE"],
    "Apache Unomi": ["LICENSE"],
    "OpenFGA": ["LICENSE"],
    "Klaro": ["LICENSE"],
    "dedupe": ["LICENSE"],
    "OpenCATS": ["LICENSE.md"],
    "Frappe HR": ["license.txt"],
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def tree_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file() and not path.is_symlink())

result = []
for name, folder in REPOS.items():
    repo = LAB / "repos" / folder
    licenses = []
    for relative in LICENSE_FILES[name]:
        file_path = repo / relative
        data = file_path.read_bytes()
        lines = data.decode("utf-8", errors="replace").splitlines()
        licenses.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "first_nonempty_lines": [line.strip() for line in lines if line.strip()][:4],
            }
        )
    security = [str(path.relative_to(repo)) for path in repo.rglob("SECURITY*") if path.is_file()]
    result.append(
        {
            "candidate": name,
            "repository": git(repo, "remote", "get-url", "origin"),
            "commit": git(repo, "rev-parse", "HEAD"),
            "commit_date": git(repo, "show", "-s", "--format=%cI", "HEAD"),
            "exact_tag": git(repo, "describe", "--tags", "--exact-match", "HEAD") if subprocess.run(["git", "-C", str(repo), "describe", "--tags", "--exact-match", "HEAD"], capture_output=True).returncode == 0 else "",
            "source_tree_bytes": tree_bytes(repo),
            "licenses": licenses,
            "security_files": sorted(security)[:20],
        }
    )
out = LAB / "artifacts" / "candidate-metadata.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "candidates": len(result), "output": str(out), "commits": {item['candidate']: item['commit'] for item in result}}, sort_keys=True))
