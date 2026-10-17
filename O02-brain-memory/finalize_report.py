#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

LAB = Path(__file__).resolve().parent
VAULT = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
REPORT = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O02 Brain, Memory, Retrieval and Storage OSS Lab Report.md"
RECEIPT = VAULT / "04_Logs/Runs/Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab.md"
PRE = LAB / "artifacts/pre-receipt-validation.json"

if not RECEIPT.is_file() or RECEIPT.stat().st_size == 0:
    raise RuntimeError("dated run receipt is missing")
if json.loads(PRE.read_text()).get("status") != "PASS":
    raise RuntimeError("pre-receipt validation is not PASS")

text = REPORT.read_text(encoding="utf-8")
replacements = {
    "status: final-gate-pending": "status: validated-bounded-pass-with-disclosed-gaps",
    "| Dated run receipt | PENDING FINALIZATION |": "| Dated run receipt | PASS; [[Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab]] |",
}
for old, new in replacements.items():
    if old not in text:
        raise RuntimeError(f"report finalization anchor missing: {old}")
    text = text.replace(old, new, 1)
if "final-gate-pending" in text or "PENDING FINALIZATION" in text:
    raise RuntimeError("report still contains a finalization-pending marker")
REPORT.write_text(text, encoding="utf-8")
print(json.dumps({
    "report": str(REPORT),
    "bytes": REPORT.stat().st_size,
    "sha256": hashlib.sha256(REPORT.read_bytes()).hexdigest(),
    "receipt": str(RECEIPT),
    "receipt_sha256": hashlib.sha256(RECEIPT.read_bytes()).hexdigest(),
    "status": "validated-bounded-pass-with-disclosed-gaps",
}, indent=2, sort_keys=True))
