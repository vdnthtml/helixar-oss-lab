#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
REPOS = ROOT / "repos"

def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

records = []
for repo in sorted(p for p in REPOS.iterdir() if (p / ".git").exists()):
    names = git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    license_paths = [
        name for name in names
        if pathlib.PurePosixPath(name).name.lower() in {
            "license", "license.md", "license.txt", "license.rst", "copying", "copying.md", "notice", "notice.txt"
        }
    ]
    top_docs = [
        name for name in names
        if "/" not in name and pathlib.PurePosixPath(name).name.lower() in {
            "readme", "readme.md", "readme.rst", "package.json", "pyproject.toml", "setup.py", "setup.cfg", "go.mod", "cargo.toml", "description"
        }
    ]
    commit = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    record = {
        "candidate": repo.name,
        "repository": git(repo, "remote", "get-url", "origin"),
        "commit": commit,
        "commit_date": git(repo, "show", "-s", "--format=%cI", "HEAD"),
        "tree_hash": tree,
        "default_ref": git(repo, "symbolic-ref", "refs/remotes/origin/HEAD") if (repo / ".git/refs/remotes/origin/HEAD").exists() else "",
        "exact_tags": git(repo, "tag", "--points-at", "HEAD").splitlines(),
        "license_paths": license_paths,
        "top_docs": top_docs,
        "tracked_path_count": len(names),
        "inspection_commands": [
            "git ls-tree -r --name-only HEAD",
            "git rev-parse HEAD",
            "git rev-parse HEAD^{tree}",
            "git show -s --format=%cI HEAD",
            "git tag --points-at HEAD",
            "git remote get-url origin",
        ],
    }
    records.append(record)

out = ROOT / "artifacts/source-tree-manifest.json"
out.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(out)
print(json.dumps(records, indent=2))
