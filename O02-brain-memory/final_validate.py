#!/usr/bin/env python3
"""Final structural/evidence gate for the O02 isolated OSS lab."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

LAB = Path("/Users/vedantswami/Projects/helixar-oss-labs/O02-brain-memory")
DYSTOPIA = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
OUTPUT = DYSTOPIA / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O02-brain-memory"
REPORT = DYSTOPIA / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O02 Brain, Memory, Retrieval and Storage OSS Lab Report.md"
RECEIPT = DYSTOPIA / "04_Logs/Runs/Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab.md"
CSV_NAMES = [
    "candidate-inventory.csv",
    "license-and-security.csv",
    "deployment-smoke-results.csv",
    "resource-profile.csv",
    "contract-fit.csv",
    "cleanup-manifest.csv",
]
CANDIDATES = {"LETTA", "MEM0", "GRAPHITI", "LLAMAINDEX", "UNSTRUCTURED", "PGVECTOR", "QDRANT", "MINIO"}
CANDIDATE_PORTS = {5432, 6333, 6334, 7474, 7687, 9000, 9001}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def run(*argv: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def main() -> int:
    checks: dict[str, Any] = {}
    required = [REPORT, RECEIPT, *(OUTPUT / name for name in CSV_NAMES)]
    checks["deliverables_exist"] = all(path.is_file() and path.stat().st_size > 0 for path in required)

    parsed = {name: rows(OUTPUT / name) for name in CSV_NAMES}
    inventory_ids = {row["candidate_id"] for row in parsed["candidate-inventory.csv"]}
    checks["candidate_inventory_exact_8"] = inventory_ids == CANDIDATES and len(parsed["candidate-inventory.csv"]) == 8
    checks["license_security_exact_8"] = {row["candidate_id"] for row in parsed["license-and-security.csv"]} == CANDIDATES
    checks["resource_exact_8"] = {row["candidate_id"] for row in parsed["resource-profile.csv"]} == CANDIDATES
    checks["contract_fit_exact_8"] = {row["candidate_id"] for row in parsed["contract-fit.csv"]} == CANDIDATES

    smoke = {row["test_id"]: row for row in parsed["deployment-smoke-results.csv"]}
    checks["three_memory_retrieval_candidates_exercised"] = (
        smoke.get("LLAMAINDEX-CORE", {}).get("status") == "PASS"
        and smoke.get("GRAPHITI-KUZU-FINGERPRINTED", {}).get("status", "").startswith("PASS")
        and smoke.get("LLAMAINDEX-QDRANT", {}).get("status") == "PASS"
    )
    checks["storage_combination_pass"] = smoke.get("LLAMAINDEX-QDRANT", {}).get("status") == "PASS"
    checks["unstructured_ingestion_pass"] = smoke.get("UNSTRUCTURED-TEXT", {}).get("status") == "PASS"
    checks["falsification_failures_retained"] = all(
        smoke.get(test_id, {}).get("status", "").startswith("FAIL")
        for test_id in ["MEM0-CONCURRENCY-HISTORICAL", "MEM0-ORDER-HISTORICAL"]
    )
    repeats = [smoke.get(f"MEM0-FINGERPRINTED-REPEAT-{n}", {}) for n in (1, 2, 3)]
    checks["mem0_flakiness_preserved"] = (
        [row.get("status") for row in repeats] == ["PASS", "FLAKY_PARTIAL", "PASS"]
        and len({row.get("fixture_sha256") for row in repeats}) == 1
        and len({row.get("environment_freeze_sha256") for row in repeats}) == 1
        and all(row.get("fixture_sha256") and row.get("environment_freeze_sha256") for row in repeats)
    )

    evidence_failures: list[str] = []
    for row in parsed["deployment-smoke-results.csv"]:
        if not row.get("command"):
            continue
        for prefix in ("stdout", "stderr"):
            path_text = row.get(f"{prefix}_path", "")
            digest = row.get(f"{prefix}_sha256", "")
            if not path_text or not digest:
                evidence_failures.append(f"{row['test_id']}:{prefix}:missing-reference")
                continue
            path = Path(path_text)
            if not path.is_file() or sha256(path) != digest:
                evidence_failures.append(f"{row['test_id']}:{prefix}:missing-or-hash-mismatch")
    checks["smoke_evidence_hashes_valid"] = not evidence_failures

    process_rows = [json.loads(line) for line in (LAB / "process-log.jsonl").read_text().splitlines() if line.strip()]
    sequences = [int(row["sequence"]) for row in process_rows]
    checks["process_sequence_unique_contiguous"] = len(sequences) == len(set(sequences)) and set(sequences) == set(range(1, max(sequences) + 1))
    checks["process_sequence_allocator_consistent"] = int((LAB / ".process-sequence").read_text().strip()) in {max(sequences), max(sequences) + 1}

    source_manifest = json.loads((LAB / "source-hash-manifest.json").read_text())
    source_csv = [item for item in source_manifest if item["role"] == "source_csv"]
    source_csv_drift = [item["path"] for item in source_csv if not Path(item["path"]).is_file() or sha256(Path(item["path"])) != item["sha256"]]
    all_source_drift = [item["path"] for item in source_manifest if not Path(item["path"]).is_file() or sha256(Path(item["path"])) != item["sha256"]]
    checks["frozen_source_csv_unchanged"] = not source_csv_drift

    repo_failures: list[dict[str, str]] = []
    for item in json.loads((LAB / "candidate-source-manifest.json").read_text()):
        repo = Path(item["path"])
        head = run("git", "rev-parse", "HEAD", cwd=repo)
        status = run("git", "status", "--porcelain", cwd=repo)
        if head.returncode != 0 or head.stdout.strip() != item["commit"] or status.returncode != 0 or status.stdout.strip():
            repo_failures.append({"candidate": item["candidate"], "head": head.stdout.strip(), "status": status.stdout.strip()})
    checks["candidate_repositories_clean_exact_commits"] = not repo_failures

    listener = run("lsof", "-nP", "-iTCP", "-sTCP:LISTEN")
    candidate_listeners = []
    if listener.returncode in {0, 1}:
        for line in listener.stdout.splitlines()[1:]:
            if any(f":{port} " in line or line.rstrip().endswith(f":{port} (LISTEN)") for port in CANDIDATE_PORTS):
                candidate_listeners.append(line)
    checks["no_candidate_listeners"] = listener.returncode in {0, 1} and not candidate_listeners

    process = run("ps", "-axo", "pid=,command=")
    candidate_processes = []
    markers = ("mem0_fixture.py", "llamaindex_qdrant_fixture.py", "unstructured_fixture.py", "graphiti_kuzu_fixture.py", "qdrant --", "minio server", "postgres -D")
    for line in process.stdout.splitlines():
        if any(marker in line for marker in markers) and "final_validate.py" not in line:
            candidate_processes.append(line.strip())
    checks["no_candidate_processes"] = process.returncode == 0 and not candidate_processes

    outputs = {
        str(path): {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in required
        if path.is_file()
    }
    critical = [
        "deliverables_exist",
        "candidate_inventory_exact_8",
        "license_security_exact_8",
        "resource_exact_8",
        "contract_fit_exact_8",
        "three_memory_retrieval_candidates_exercised",
        "storage_combination_pass",
        "unstructured_ingestion_pass",
        "falsification_failures_retained",
        "mem0_flakiness_preserved",
        "smoke_evidence_hashes_valid",
        "process_sequence_unique_contiguous",
        "process_sequence_allocator_consistent",
        "frozen_source_csv_unchanged",
        "candidate_repositories_clean_exact_commits",
        "no_candidate_listeners",
        "no_candidate_processes",
    ]
    result = {
        "status": "PASS_BOUNDED_WITH_DISCLOSED_GAPS" if all(checks[name] for name in critical) else "FAIL",
        "checks": checks,
        "counts": {
            "process_records_visible_before_validator_receipt": len(process_rows),
            "process_max_sequence_visible": max(sequences),
            "network_command_envelopes": sum(row["kind"] == "network" for row in process_rows),
            "local_command_envelopes": sum(row["kind"] == "local" for row in process_rows),
            "candidate_families": len(inventory_ids),
            "smoke_rows": len(smoke),
            "frozen_source_csv_files": len(source_csv),
        },
        "known_gaps": [
            "The original broad source manifest drifted because shared current-state/control/daily notes changed concurrently; frozen R01-R10 evidence CSVs remained unchanged.",
            "Initial candidate venv diagnostics were contaminated by inherited Python environment variables; sanitized pip check passed in all four isolated environments.",
            "pip-audit found advisories in pip/setuptools build tooling; no audited candidate runtime package was named.",
            "Qdrant was exercised only in embedded mode; PostgreSQL+pgvector, Qdrant server and MinIO server were not run.",
            "Graphiti proof is deprecated-Kuzu graph CRUD only, not episode extraction or temporal search.",
            "Network denial was process-local socket guarding, not an OS-level sandbox.",
        ],
        "evidence_failures": evidence_failures,
        "source_csv_drift": source_csv_drift,
        "broad_source_drift": all_source_drift,
        "repository_failures": repo_failures,
        "candidate_listeners": candidate_listeners,
        "candidate_processes": candidate_processes,
        "deliverables": outputs,
    }
    (LAB / "validation-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
