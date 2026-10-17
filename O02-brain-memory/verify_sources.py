#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
manifest_path = ROOT / "source-hash-manifest.json"
records = json.loads(manifest_path.read_text(encoding="utf-8"))
results = []
for record in records:
    path = pathlib.Path(record["path"])
    exists = path.exists()
    current = None
    size = None
    if exists:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        current = digest.hexdigest()
        size = path.stat().st_size
    results.append({
        "path": str(path),
        "exists": exists,
        "expected_sha256": record["sha256"],
        "current_sha256": current,
        "expected_bytes": record["bytes"],
        "current_bytes": size,
        "unchanged": exists and current == record["sha256"] and size == record["bytes"],
    })
output = {
    "manifest": str(manifest_path),
    "files_checked": len(results),
    "all_unchanged": all(row["unchanged"] for row in results),
    "changed": [row for row in results if not row["unchanged"]],
    "results": results,
}
output_path = ROOT / "source-immutability-verification.json"
output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({key: output[key] for key in ("files_checked", "all_unchanged", "changed")}, indent=2, sort_keys=True))
sys.exit(0 if output["all_unchanged"] else 1)
