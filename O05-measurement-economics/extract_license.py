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
manifest = json.loads((ROOT / "artifacts/source-tree-manifest.json").read_text())
record = next(item for item in manifest if item["candidate"] == candidate)
out_root = ROOT / "artifacts" / "licenses" / candidate
results = []
for path in record["license_paths"]:
    try:
        blob = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=repo)
        status = "READ"
        error = ""
    except subprocess.CalledProcessError as exc:
        blob = b""
        status = "ERROR"
        error = str(exc)
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
result_path = ROOT / "artifacts" / "licenses" / f"{candidate}-manifest.json"
result_path.parent.mkdir(parents=True, exist_ok=True)
result_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
print(json.dumps(results, indent=2))
