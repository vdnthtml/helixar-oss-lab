#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
fixture_names = [
    "mem0_fixture.py",
    "mem0_smoke.py",
    "smoke_mem0.py",
    "llamaindex_smoke.py",
    "llamaindex_qdrant_fixture.py",
    "unstructured_smoke.py",
    "unstructured_fixture.py",
    "graphiti_kuzu_fixture.py",
]
envs = ["mem0", "llamaindex", "unstructured", "graphiti"]
records = []
for name in fixture_names:
    path = ROOT / "fixtures" / name
    if path.exists():
        raw = path.read_bytes()
        records.append({"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
freezes = {}
for name in envs:
    completed = subprocess.run(
        [str(ROOT / "envs" / name / "bin" / "python"), "-m", "pip", "freeze", "--all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    text = completed.stdout
    freezes[name] = {
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "line_count": len([line for line in text.splitlines() if line.strip()]),
        "content": text.splitlines(),
    }
out = {"fixtures": records, "environment_freezes": freezes}
path = ROOT / "artifacts" / "fixture-and-environment-fingerprints.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"fixture_count": len(records), "fixtures": records, "environment_freeze_sha256": {k:v["sha256"] for k,v in freezes.items()}}, indent=2, sort_keys=True))
