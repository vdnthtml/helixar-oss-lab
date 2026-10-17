#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
candidate = sys.argv[1]
repo = ROOT / "repos" / candidate
all_names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo, text=True).splitlines()
preferred = {
    "README.md", "README.rst", "package.json", "pyproject.toml", "setup.py", "go.mod",
    "python/pyproject.toml", "python/setup.py", "dbt-metricflow/pyproject.toml",
    "client/python/pyproject.toml", "docs/README.md", "SECURITY.md", "SECURITY",
}
paths = [name for name in all_names if name in preferred]
out_root = ROOT / "artifacts" / "source-docs" / candidate
results = []
for path in paths:
    try:
        blob = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=repo)
        status, error = "READ", ""
    except subprocess.CalledProcessError as exc:
        blob, status, error = b"", "ERROR", str(exc)
    destination = out_root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    if blob:
        destination.write_bytes(blob)
    results.append({
        "path": path,
        "status": status,
        "sha256": hashlib.sha256(blob).hexdigest() if blob else "",
        "bytes": len(blob),
        "local_copy": str(destination) if blob else "",
        "error": error,
    })
manifest_path = ROOT / "artifacts" / "source-docs" / f"{candidate}-manifest.json"
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(results, indent=2))
