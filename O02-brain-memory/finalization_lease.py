#!/usr/bin/env python3
"""Prove the shared O02 lab ledger is quiet before final regeneration."""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent
LEDGER = LAB / "process-log.jsonl"
ALLOCATOR = LAB / ".process-sequence"
MUTATOR_MARKERS = (
    "generate_deliverables.py",
    "reconcile_final_deliverables.py",
    "write_run_receipt.py",
    "finalize_report.py",
    "mem0_fixture.py",
    "llamaindex_qdrant_fixture.py",
    "unstructured_fixture.py",
    "graphiti_kuzu_fixture.py",
)


def snapshot() -> dict[str, object]:
    rows = [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]
    sequences = [int(row["sequence"]) for row in rows]
    return {
        "records": len(rows),
        "max_sequence": max(sequences),
        "sequence_set_contiguous": len(sequences) == len(set(sequences)) and set(sequences) == set(range(1, max(sequences) + 1)),
        "allocator": int(ALLOCATOR.read_text().strip()),
    }


def active_mutators() -> list[str]:
    own_pid = os.getpid()
    output = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="], text=True, capture_output=True, check=True
    ).stdout
    active: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            pid = int(stripped.split(None, 1)[0])
        except ValueError:
            continue
        if pid == own_pid:
            continue
        if any(marker in stripped for marker in MUTATOR_MARKERS) and "finalization_lease.py" not in stripped:
            active.append(stripped)
    return active


def main() -> int:
    first = snapshot()
    active_first = active_mutators()
    time.sleep(5)
    second = snapshot()
    active_second = active_mutators()
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "quiet_seconds": 5,
        "first": first,
        "second": second,
        "active_mutators_first": active_first,
        "active_mutators_second": active_second,
        "stable": first == second,
        "pass": first == second and not active_first and not active_second and bool(second["sequence_set_contiguous"]),
    }
    out = LAB / "artifacts/finalization-lease.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
