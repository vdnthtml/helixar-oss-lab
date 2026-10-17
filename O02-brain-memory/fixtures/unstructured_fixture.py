#!/usr/bin/env python3
"""Offline deterministic Unstructured text-partition lineage fixture."""
from __future__ import annotations

import hashlib
import json
import shutil
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "storage" / "unstructured-fixture"
EXPORT = ROOT / "exports" / "unstructured-fixture-export.json"
SOURCE_TEXT = """Synthetic Policy Packet

Alpha launch policy is approved for the isolated fixture.

Beta finance policy remains a separate evidence record.
"""

from unstructured.partition.text import partition_text  # noqa: E402


def project(elements):
    projected = []
    for element in elements:
        payload = element.to_dict()
        metadata = payload.get("metadata", {})
        projected.append(
            {
                "type": payload.get("type"),
                "text": payload.get("text"),
                "element_id": payload.get("element_id"),
                "filename": metadata.get("filename"),
                "file_directory": metadata.get("file_directory"),
                "filetype": metadata.get("filetype"),
                "languages": metadata.get("languages"),
            }
        )
    return projected


def main() -> int:
    shutil.rmtree(STATE, ignore_errors=True)
    STATE.mkdir(parents=True, exist_ok=True)
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    source = STATE / "fixture-policy.txt"
    source.write_text(SOURCE_TEXT)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    denied_egress = []
    original_connect = socket.socket.connect

    def guarded_connect(sock, address):
        if isinstance(address, tuple) and address:
            host = str(address[0]).lower()
            if host not in {"127.0.0.1", "::1", "localhost"}:
                denied_egress.append(repr(address))
                raise RuntimeError(f"external egress denied by fixture: {address!r}")
        return original_connect(sock, address)

    socket.socket.connect = guarded_connect
    try:
        first = project(partition_text(filename=str(source), languages=["eng"]))
        second = project(partition_text(filename=str(source), languages=["eng"]))
        assert first == second
        assert len(first) >= 3
        assert all(row["filename"] == source.name for row in first)
        assert all(row["filetype"] == "text/plain" for row in first)
        assert any("Alpha launch policy" in row["text"] for row in first)
        assert any("Beta finance policy" in row["text"] for row in first)

        def run_partition(_):
            return project(partition_text(filename=str(source), languages=["eng"]))

        with ThreadPoolExecutor(max_workers=3) as pool:
            concurrent = list(pool.map(run_partition, range(6)))
        assert all(rows == first for rows in concurrent)

        payload = {
            "candidate": "Unstructured",
            "source": {
                "path": str(source),
                "sha256": source_sha,
                "synthetic_identity": "fixture-policy@o02.invalid",
            },
            "elements": first,
        }
        EXPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        reloaded = json.loads(EXPORT.read_text())
        assert reloaded["source"]["sha256"] == source_sha
        assert reloaded["elements"] == first
        assert not denied_egress

        summary = {
            "candidate": "Unstructured",
            "status": "PASS",
            "public_api": ["unstructured.partition.text.partition_text", "Element.to_dict"],
            "external_egress_attempts": denied_egress,
            "checks": {
                "source_lineage_round_trip": True,
                "deterministic_partition_repetitions": 2,
                "concurrent_deterministic_partitions": len(concurrent),
                "export_reload": True,
                "element_count": len(first),
            },
            "source_sha256": source_sha,
            "export_path": str(EXPORT),
            "proof_boundary": "Text ingestion and lineage transformation only; memory promotion, revocation, retrieval, and truth governance remain external responsibilities.",
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    finally:
        socket.socket.connect = original_connect


if __name__ == "__main__":
    raise SystemExit(main())
