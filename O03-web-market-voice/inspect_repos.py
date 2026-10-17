#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOS = ROOT / "repos"
NAMES = [
    "lighthouse", "crawlee", "unlighthouse", "siteone", "changedetection",
    "readability", "openrefine", "splink", "dedupe", "taguette", "doccano",
    "argilla", "formbricks", "whisper", "bertopic",
]


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def archive_hash(repo: Path) -> str:
    proc = subprocess.Popen(["git", "-C", str(repo), "archive", "HEAD"], stdout=subprocess.PIPE)
    h = hashlib.sha256()
    assert proc.stdout is not None
    stream = proc.stdout
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    code = proc.wait()
    if code:
        raise RuntimeError(f"git archive failed for {repo}: {code}")
    return h.hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    out = []
    for name in NAMES:
        repo = REPOS / name
        tracked = git(repo, "ls-files").splitlines()
        license_candidates = []
        for rel in tracked:
            parts = Path(rel).parts
            base = parts[-1].lower()
            if len(parts) <= 4 and re.match(r"^(license|licence|copying|notice)(\..*)?$", base):
                p = repo / rel
                if p.is_file():
                    text = p.read_text(encoding="utf-8", errors="replace")
                    license_candidates.append({
                        "path": rel,
                        "sha256": file_sha(p),
                        "bytes": p.stat().st_size,
                        "first_300": " ".join(text[:300].split()),
                    })
        manifests = [
            rel for rel in tracked
            if Path(rel).name in {
                "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
                "pyproject.toml", "requirements.txt", "requirements-dev.txt", "Pipfile.lock",
                "poetry.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
                "pom.xml", "build.gradle", "build.gradle.kts", "composer.json", "composer.lock",
            } and len(Path(rel).parts) <= 3
        ]
        security = [rel for rel in tracked if Path(rel).name.lower() in {"security.md", "security.txt"} and len(Path(rel).parts) <= 4]
        du_kb = int(subprocess.check_output(["du", "-sk", str(repo)], text=True).split()[0])
        try:
            describe = git(repo, "describe", "--tags", "--exact-match", "HEAD")
        except subprocess.CalledProcessError:
            describe = ""
        out.append({
            "name": name,
            "repository": git(repo, "remote", "get-url", "origin"),
            "commit": git(repo, "rev-parse", "HEAD"),
            "tree": git(repo, "rev-parse", "HEAD^{tree}"),
            "commit_date": git(repo, "show", "-s", "--format=%cI", "HEAD"),
            "head_tag": describe,
            "archive_sha256": archive_hash(repo),
            "disk_kb": du_kb,
            "license_files": license_candidates,
            "manifests": manifests,
            "security_policy_files": security,
        })
    (ROOT / "source-metadata.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
