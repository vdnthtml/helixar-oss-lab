#!/usr/bin/env python3
"""Offline Unstructured Markdown lineage and round-trip smoke fixture."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE_ROOT = ROOT / "storage" / "unstructured"
EXPORT_ROOT = ROOT / "exports"
STATE_ROOT.mkdir(parents=True, exist_ok=True)
EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
run_dir = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=STATE_ROOT))

os.environ["DO_NOT_TRACK"] = "1"
os.environ["SCARF_NO_ANALYTICS"] = "1"
os.environ["UNSTRUCTURED_TELEMETRY_ENABLED"] = "0"

from unstructured.partition.md import partition_md
from unstructured.staging.base import elements_from_json, elements_to_json

markdown_text = """# ROOT

## CHILD

- OFFLINE LINEAGE ITEM
- SECOND LINEAGE ITEM
"""

def partition_once():
    return partition_md(
        text=markdown_text,
        metadata_filename="fixtures.invalid/source.md",
        metadata_last_modified="2000-01-01T00:00:00+0000",
        languages=[""],
        unique_element_ids=False,
    )

first = partition_once()
second = partition_once()
assert first
assert [element.id for element in first] == [element.id for element in second]
assert [element.to_dict() for element in first] == [element.to_dict() for element in second]
assert all(element.metadata.filename == "source.md" for element in first)
assert all(element.metadata.file_directory == "fixtures.invalid" for element in first)
assert all(element.metadata.filetype == "text/markdown" for element in first)
assert all(element.metadata.last_modified == "2000-01-01T00:00:00+0000" for element in first)
ids = {element.id for element in first}
assert any(element.metadata.parent_id in ids for element in first if element.metadata.parent_id)

payload = elements_to_json(first, indent=2)
reloaded = elements_from_json(text=payload)
assert [element.to_dict() for element in reloaded] == [element.to_dict() for element in first]

export_path = EXPORT_ROOT / "unstructured-elements.json"
export_path.write_text(payload + "\n", encoding="utf-8")
summary = {
    "candidate": "Unstructured",
    "run_dir": str(run_dir),
    "element_count": len(first),
    "deterministic_ids": [element.id for element in first],
    "lineage_parent_ids": [element.metadata.parent_id for element in first],
    "round_trip_equal": True,
    "export_path": str(export_path),
    "export_sha256": hashlib.sha256((payload + "\n").encode()).hexdigest(),
    "telemetry_env": {key: os.environ[key] for key in ("DO_NOT_TRACK", "SCARF_NO_ANALYTICS", "UNSTRUCTURED_TELEMETRY_ENABLED")},
    "hosted_provider_calls": 0,
    "external_business_writes": 0,
}
print(json.dumps(summary, indent=2, sort_keys=True))
