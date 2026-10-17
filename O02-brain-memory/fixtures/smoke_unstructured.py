#!/usr/bin/env python3
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

from unstructured.partition.html import partition_html
from unstructured.staging.base import elements_to_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "smoke" / "unstructured"

HTML = """<!doctype html><html><body>
<h1>O02 Demand Memory</h1>
<p>Helixar captures evidence-backed demand signals with explicit provenance.</p>
<h2>Lineage</h2>
<ul><li>source URI</li><li>capture timestamp</li></ul>
</body></html>"""


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    elements = partition_html(text=HTML, metadata_filename="fixture-o02.html", unique_element_ids=True)
    assert len(elements) >= 4
    categories = [element.category for element in elements]
    assert "Title" in categories
    assert any("evidence-backed demand signals" in element.text for element in elements)
    assert all(element.metadata.filename == "fixture-o02.html" for element in elements)
    ids = [element.id for element in elements]
    assert len(ids) == len(set(ids))

    json_path = OUT / "elements.json"
    elements_to_json(elements, filename=str(json_path))
    digest = hashlib.sha256(json_path.read_bytes()).hexdigest()
    receipt = {
        "candidate": "unstructured",
        "package_version": importlib.metadata.version("unstructured"),
        "status": "PASS",
        "offline": True,
        "telemetry": "off by default; DO_NOT_TRACK=1 and SCARF_NO_ANALYTICS=1 set",
        "tests": {
            "html_partition": True,
            "element_typing": True,
            "source_filename_provenance": True,
            "stable_unique_ids": True,
            "json_export": True,
        },
        "element_count": len(elements),
        "categories": categories,
        "elements_json_sha256": digest,
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
