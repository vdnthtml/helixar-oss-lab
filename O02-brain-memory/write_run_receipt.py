#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent
VAULT = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
DATA = VAULT / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O02-brain-memory"
REPORT = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O02 Brain, Memory, Retrieval and Storage OSS Lab Report.md"
RECEIPT = VAULT / "04_Logs/Runs/Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab.md"
CSV_NAMES = [
    "candidate-inventory.csv",
    "license-and-security.csv",
    "deployment-smoke-results.csv",
    "resource-profile.csv",
    "contract-fit.csv",
    "cleanup-manifest.csv",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


pre = json.loads((LAB / "artifacts/pre-receipt-validation.json").read_text())
if pre.get("status") != "PASS":
    raise RuntimeError("pre-receipt validation did not pass")

processes = [json.loads(line) for line in (LAB / "process-log.jsonl").read_text().splitlines() if line.strip()]
network = [json.loads(line) for line in (LAB / "network-fetch-log.jsonl").read_text().splitlines() if line.strip()]
by_seq = {int(row["sequence"]): row for row in processes}
smoke = {row["test_id"]: row for row in csv_rows("deployment-smoke-results.csv")}
inventory = csv_rows("candidate-inventory.csv")
licenses = csv_rows("license-and-security.csv")
source_manifest = json.loads((LAB / "source-hash-manifest.json").read_text())
source_csv = [row for row in source_manifest if row["role"] == "source_csv"]
source_csv_unchanged = all(Path(row["path"]).is_file() and sha256(Path(row["path"])) == row["sha256"] for row in source_csv)

artifact_lines = []
for path in [REPORT, *(DATA / name for name in CSV_NAMES)]:
    artifact_lines.append(f"- `{path}` — {path.stat().st_size} bytes; SHA-256 `{sha256(path)}` at receipt generation; detached post-receipt hashes are authoritative")

def ev(sequence: int) -> str:
    row = by_seq[sequence]
    return (
        f"sequence {sequence} `{row['label']}` exit `{row['exit_code']}`; "
        f"stdout `{row['stdout_path']}` SHA-256 `{row['stdout_sha256']}`; "
        f"stderr `{row['stderr_path']}` SHA-256 `{row['stderr_sha256']}`"
    )

critical_sequences = [32, 48, 50, 73, 75, 76, 77, 78, 91, 92, 93]
critical_lines = "\n".join(f"- {ev(seq)}" for seq in critical_sequences)
classification_lines = "\n".join(
    f"- **{row['candidate']}** (`{row['candidate_id']}`): `{row['classification']}` — {row['proof_boundary']}"
    for row in inventory
)
license_lines = "\n".join(
    f"- `{row['candidate_id']}`: `{row['license_spdx']}` at `{row['commit']}`; adoption status `{row['code_adoption_status']}`."
    for row in licenses
)

receipt = f"""---
title: Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab
date: 2026-07-14
finalized_utc: {datetime.now(timezone.utc).isoformat()}
status: pass-bounded-with-disclosed-gaps
wave: A
lane: O02
---

# Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab

Links: [[O02 Brain, Memory, Retrieval and Storage OSS Lab Report]] · [[00 Helixar World-Class Benchmark Program - Control Center]] · [[04 Cross-Packet Implementation Readiness Audit - 2026-07-14]]

## Outcome

**PASS_BOUNDED_WITH_DISCLOSED_GAPS.** The O02 audit inspected all eight candidate families at exact commits, retained license/security/telemetry findings, executed deterministic local fixtures, produced the report plus six required CSVs, and passed the pre-receipt structural/evidence gate. This receipt is not production approval.

The minimum executable proof was met without counting flaky Mem0 as a clean pass:

- LlamaIndex local retrieval: `{smoke['LLAMAINDEX-CORE']['status']}`.
- Unstructured text/concurrency ingestion: `{smoke['UNSTRUCTURED-TEXT']['status']}`.
- Graphiti local Kuzu graph-storage CRUD: `{smoke['GRAPHITI-KUZU-FINGERPRINTED']['status']}` (bounded/deprecated-backend proof only).
- LlamaIndex + persistent embedded Qdrant combination: `{smoke['LLAMAINDEX-QDRANT']['status']}`.
- Mem0 repeated current fixture: `PASS`, `FLAKY_PARTIAL`, `PASS`; aggregate disposition remains `FLAKY/PARTIAL`.

## Candidate denominator and dispositions

All **{len(inventory)}** required candidate families are represented exactly once in the inventory.

{classification_lines}

## License and security boundary

{license_lines}

Telemetry was explicitly disabled in exercised paths. Qdrant server, PostgreSQL+pgvector, MinIO server, Letta runtime, Graphiti production graph backends, Graphiti LLM extraction, and all HA/auth/backup paths remain unproven. The isolated Python environments passed sanitized `pip check` at sequence 73. `pip-audit` findings affected lab installer/build tooling, not the named exercised candidate runtime packages.

## Exact executable evidence

{critical_lines}

Fixture and environment hashes are retained in `{LAB / 'artifacts/fixture-and-environment-fingerprints.json'}` and copied into the applicable rows of `deployment-smoke-results.csv`.

## External-effect and network accounting

- Process records visible before this receipt command: **{len(processes)}**; maximum sequence **{max(by_seq)}**.
- Recorded public-network command envelopes: **{len(network)}**.
- Lower-level HTTP request count inside Git/pip: **UNKNOWN_NOT_PACKET_CAPTURED**.
- Loopback command envelopes: **{sum(row.get('kind') == 'loopback' for row in processes)}**.
- External business-system writes: **0**.
- Credentials, customer data, production connectors, CMS/CRM mutation, publishing, spend and outbound actions: **0**.
- Persistent candidate services: **0**; candidate ports were free at the pre-receipt gate.
- Fixture socket guards recorded zero attempted external egress in the passing bounded paths. This was process-local guarding, not an OS-level sandbox.

## Source immutability and concurrency disclosure

- Frozen R01-R10 source/evidence CSVs checked: **{len(source_csv)}**; unchanged: **{source_csv_unchanged}**.
- Candidate source repositories were clean, at exact recorded commits and tree hashes, at the pre-receipt gate.
- Shared current-state/control/daily notes drifted during parallel program work and are disclosed in the report; O02 did not overwrite or roll them back.
- Finalization lease: sequence 91 observed a five-second quiet ledger interval with no active mutators before the canonical generator replay.
- Canonical late-evidence generator replay: sequence 92, exit 0.
- Pre-receipt structural/evidence gate after replay: sequence 93, exit 0.

## Deliverables and receipt-time hashes

{chr(10).join(artifact_lines)}

The detached final gate writes `{LAB / 'artifacts/final-validation.json'}` after the receipt and report status are finalized; that artifact is the authoritative post-write hash manifest.

## Cleanup state

- No candidate service/process requires termination.
- Source checkouts are retained for reproducibility.
- Isolated venvs are ready for cleanup after handoff.
- Synthetic fixture state and exports remain under `{LAB}` and contain no customer/business data.
- Exact cleanup paths and dispositions are in [[cleanup-manifest]].

## Decisions still requiring human approval

1. Whether to run a dedicated PostgreSQL+pgvector server/backup/tenant-isolation lab.
2. Whether Qdrant server merits an auth/telemetry/replication/backup POC or remains embedded/derived only.
3. Whether Mem0 receives a serialized/server-writer idempotency POC or remains only a contract/fixture reference.
4. Whether Graphiti's temporal graph value justifies a supported graph database plus structured-output LLM POC.
5. Which S3-compatible object store to adopt; direct MinIO community-source code adoption is rejected pending legal/commercial review.
6. Whether current Letta Agent SDK/App Server merits a separately scoped Node runtime audit.

## Acceptance boundary

This run proves bounded localhost/file-backed deployability for selected adapters and documents unproven production surfaces. It does **not** authorize production adoption, live data, credentials, outbound traffic, infrastructure deployment or business-system mutation.
"""
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(receipt, encoding="utf-8")
print(json.dumps({
    "receipt": str(RECEIPT),
    "bytes": RECEIPT.stat().st_size,
    "sha256": sha256(RECEIPT),
    "candidate_rows": len(inventory),
    "process_records_before_receipt": len(processes),
    "public_network_command_envelopes": len(network),
    "source_csv_unchanged": source_csv_unchanged,
}, indent=2, sort_keys=True))
