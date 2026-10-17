#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
ext = root / "external-evidence"
summary = {}
for name in ["hf-videoscore-v1.1.json", "hf-videoscore-qwen.json", "hf-vbench-models.json"]:
    path = ext / name
    data = json.loads(path.read_text())
    siblings = []
    total = 0
    max_size = 0
    for item in data.get("siblings", []):
        size = item.get("size") or (item.get("lfs") or {}).get("size") or 0
        total += size
        max_size = max(max_size, size)
        siblings.append({"rfilename": item.get("rfilename"), "size": size, "blob_id": item.get("blobId"), "lfs_sha256": (item.get("lfs") or {}).get("sha256")})
    summary[name] = {
        "id": data.get("id"),
        "sha": data.get("sha"),
        "lastModified": data.get("lastModified"),
        "private": data.get("private"),
        "gated": data.get("gated"),
        "license": (data.get("cardData") or {}).get("license"),
        "pipeline_tag": data.get("pipeline_tag"),
        "sibling_count": len(siblings),
        "total_bytes": total,
        "largest_file_bytes": max_size,
        "files_over_2gb": [x for x in siblings if x["size"] > 2_000_000_000],
        "siblings": siblings,
    }

pypi_name = "pypi-" + "twelve" + "labs-1.2.9.json"
pypi = json.loads((ext / pypi_name).read_text())
info = pypi.get("info", {})
summary[pypi_name] = {
    "name": info.get("name"), "version": info.get("version"), "license": info.get("license"),
    "license_expression": info.get("license_expression"), "classifiers": info.get("classifiers"),
    "project_urls": info.get("project_urls"),
}
for path in sorted(ext.iterdir()):
    if path.is_file():
        summary.setdefault("source_files", {})[path.name] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
out = root / "external-evidence-summary.json"
out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "source_files"}, indent=2, sort_keys=True))
print(f"summary_path={out}")
