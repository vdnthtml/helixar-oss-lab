#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pathlib
import re
import socket
import subprocess

LAB = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
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
CANDIDATES = {"LETTA", "MEM0", "GRAPHITI", "LLAMAINDEX", "UNSTRUCTURED", "PGVECTOR", "QDRANT", "MINIO"}

parser = argparse.ArgumentParser()
parser.add_argument("--phase", choices=["pre", "final"], required=True)
args = parser.parse_args()
errors: list[str] = []
checks: dict[str, object] = {}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA / name
    if not path.exists():
        errors.append(f"missing CSV: {path}")
        return []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:
        errors.append(f"CSV parse failed {path}: {exc}")
        return []
    if not rows:
        errors.append(f"CSV has no data rows: {path}")
    if any(None in row for row in rows):
        errors.append(f"CSV has surplus/malformed columns: {path}")
    return rows

# Existence and schema checks.
required = [REPORT, *(DATA / name for name in CSV_NAMES)]
if args.phase == "final":
    required.append(RECEIPT)
for path in required:
    if not path.exists():
        errors.append(f"missing required output: {path}")
checks["required_outputs"] = {str(path): path.exists() for path in required}

schemas = {
    "candidate-inventory.csv": {"candidate_id","candidate","exact_commit","source_inspected","classification","proof_boundary"},
    "license-and-security.csv": {"candidate_id","commit","license_spdx","license_sha256","telemetry_default","code_adoption_status"},
    "deployment-smoke-results.csv": {"test_id","candidate_id","proof_level","status","stdout_path","stdout_sha256","stderr_path","stderr_sha256","fixture_sha256","environment_freeze_sha256"},
    "resource-profile.csv": {"candidate_id","status","measurement_evidence","limitations"},
    "contract-fit.csv": {"candidate_id","capability","fixture_proof","fit_status","risk","evidence"},
    "cleanup-manifest.csv": {"item_id","candidate_id","path_or_resource","cleanup_action","status","verification"},
}
tables: dict[str, list[dict[str, str]]] = {}
for name in CSV_NAMES:
    rows = read_csv(name)
    tables[name] = rows
    if rows:
        missing = schemas[name] - set(rows[0])
        if missing:
            errors.append(f"{name} missing columns: {sorted(missing)}")
checks["csv_row_counts"] = {name: len(rows) for name, rows in tables.items()}

inventory = tables["candidate-inventory.csv"]
ids = [row.get("candidate_id", "") for row in inventory]
if len(inventory) != 8 or set(ids) != CANDIDATES or len(ids) != len(set(ids)):
    errors.append(f"candidate denominator mismatch: rows={len(inventory)} ids={ids}")
for name in ["license-and-security.csv", "resource-profile.csv", "contract-fit.csv"]:
    got = {row.get("candidate_id", "") for row in tables[name]}
    if got != CANDIDATES:
        errors.append(f"candidate coverage mismatch in {name}: {sorted(got)}")

# Evidence-path/hash resolution.
evidence_failures = []
for row in tables["deployment-smoke-results.csv"]:
    if row.get("status") == "NOT_RUN":
        continue
    for path_key, hash_key in [("stdout_path","stdout_sha256"),("stderr_path","stderr_sha256")]:
        raw_path = row.get(path_key, "")
        raw_hash = row.get(hash_key, "")
        if not raw_path:
            evidence_failures.append(f"{row.get('test_id')} missing {path_key}")
            continue
        path = pathlib.Path(raw_path)
        if not path.exists():
            evidence_failures.append(f"{row.get('test_id')} evidence missing: {path}")
        elif raw_hash and sha256(path) != raw_hash:
            evidence_failures.append(f"{row.get('test_id')} hash mismatch: {path}")
if evidence_failures:
    errors.extend(evidence_failures)
checks["evidence_path_hash_failures"] = evidence_failures

# Source CSV immutability and disclosed mutable-context drift.
source_manifest = json.loads((LAB / "source-hash-manifest.json").read_text())
source_results = []
for record in source_manifest:
    path = pathlib.Path(record["path"])
    current = sha256(path) if path.exists() else None
    source_results.append({
        "path": str(path), "role": record["role"], "exists": path.exists(),
        "expected_sha256": record["sha256"], "current_sha256": current,
        "unchanged": current == record["sha256"],
    })
source_csv = [row for row in source_results if row["role"] == "source_csv"]
source_csv_ok = len(source_csv) == 20 and all(row["unchanged"] for row in source_csv)
if not source_csv_ok:
    errors.append("frozen R01-R10 source CSV corpus changed")
checks["source_csv_immutability"] = {"count": len(source_csv), "all_unchanged": source_csv_ok}
checks["disclosed_mandatory_context_drift"] = [row for row in source_results if row["role"] == "mandatory_context" and not row["unchanged"]]

# Candidate repository exact-root, commit, tree, and cleanliness.
repo_results = []
for record in json.loads((LAB / "candidate-source-manifest.json").read_text()):
    repo = pathlib.Path(record["path"]).resolve()
    def git(*argv: str) -> str:
        return subprocess.run(["git","-C",str(repo),*argv], text=True, capture_output=True, check=True).stdout.strip()
    try:
        root = pathlib.Path(git("rev-parse","--show-toplevel")).resolve()
        head = git("rev-parse","HEAD")
        tree = git("rev-parse","HEAD^{tree}")
        status = git("status","--porcelain")
        ok = root == repo and head == record["commit"] and tree == record["tree_hash"] and status == ""
    except Exception as exc:
        root, head, tree, status, ok = None, None, None, str(exc), False
    repo_results.append({"candidate":record["candidate"],"path":str(repo),"root":str(root) if root else None,"head":head,"tree":tree,"status":status,"pass":ok})
if not all(row["pass"] for row in repo_results):
    errors.append("candidate repository exact-root/commit/tree/cleanliness gate failed")
checks["candidate_repositories"] = repo_results

# Candidate port and process cleanup.
ports = [5432, 6333, 6334, 9000, 9001]
port_results = {}
for port in ports:
    sock = socket.socket()
    sock.settimeout(0.15)
    port_results[str(port)] = sock.connect_ex(("127.0.0.1", port)) != 0
    sock.close()
if not all(port_results.values()):
    errors.append(f"candidate port still reachable: {port_results}")
checks["candidate_ports_free"] = port_results
ps = subprocess.run(["ps","ax","-o","pid=,command="], text=True, capture_output=True, check=True).stdout.splitlines()
lab_processes = [line.strip() for line in ps if str(LAB) in line and "validate_deliverables.py" not in line]
if lab_processes:
    errors.append(f"lab-owned process still running: {lab_processes}")
checks["lab_owned_processes"] = lab_processes

# Network/business-effect accounting.
process_rows = [json.loads(line) for line in (LAB / "process-log.jsonl").read_text().splitlines() if line.strip()]
network_rows = [json.loads(line) for line in (LAB / "network-fetch-log.jsonl").read_text().splitlines() if line.strip()]
loopback_rows = [row for row in process_rows if row.get("kind") == "loopback"]
for row in network_rows:
    label = row.get("label", "").lower()
    if not any(token in label for token in ["clone","install","pip-audit","network"]):
        errors.append(f"unclassified network command label: {row.get('label')}")
checks["activity_accounting"] = {
    "process_records_before_current_validator": len(process_rows),
    "predicted_process_records_after_current_validator": len(process_rows) + 1,
    "public_network_command_envelopes": len(network_rows),
    "loopback_command_envelopes": len(loopback_rows),
    "external_business_writes": 0,
    "lower_level_http_request_count": "UNKNOWN_NOT_PACKET_CAPTURED",
}

# Secret-pattern scan across authored outputs and retained non-source lab evidence.
secret_patterns = {
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    "github_token": re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{16,}"),
    "google_key": re.compile(r"\bAIza[A-Za-z0-9_-]{20,}"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    "aws_access_key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._-]{24,}"),
}
scan_paths = [path for path in required if path.exists()]
for folder in [LAB / "logs", LAB / "fixtures", LAB / "artifacts"]:
    if folder.exists():
        scan_paths.extend(path for path in folder.rglob("*") if path.is_file() and path.stat().st_size < 5_000_000)
secret_hits = []
for path in scan_paths:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for name, pattern in secret_patterns.items():
        for match in pattern.finditer(text):
            secret_hits.append({"file":str(path),"pattern":name,"offset":match.start()})
if secret_hits:
    errors.append(f"secret-pattern scan found {len(secret_hits)} hits")
checks["secret_pattern_hits"] = secret_hits

# Report and receipt final-state checks.
if REPORT.exists():
    report_text = REPORT.read_text(encoding="utf-8")
    if args.phase == "final" and ("final-gate-pending" in report_text or "PENDING FINALIZATION" in report_text):
        errors.append("report still declares finalization pending")
    links = re.findall(r"\[\[([^\]]+)\]\]", report_text)
    vault_stems = {path.stem for path in VAULT.rglob("*") if path.is_file()}
    unresolved = []
    for link in links:
        target = link.split("|",1)[0].split("#",1)[0]
        if args.phase == "pre" and target == RECEIPT.stem:
            continue
        if pathlib.Path(target).name not in vault_stems:
            unresolved.append(link)
    if unresolved:
        errors.append(f"unresolved report wikilinks: {unresolved}")
    checks["report_wikilinks"] = {"count":len(links),"unresolved":unresolved}
if args.phase == "final" and RECEIPT.exists():
    receipt_text = RECEIPT.read_text(encoding="utf-8")
    if "PENDING FINALIZATION" in receipt_text or "final-gate-pending" in receipt_text:
        errors.append("receipt still declares finalization pending")

# Final hashes.
output_hashes = {}
for path in required:
    if path.exists():
        output_hashes[str(path)] = {"bytes":path.stat().st_size,"sha256":sha256(path)}
checks["output_hashes"] = output_hashes

result = {"phase":args.phase,"status":"PASS" if not errors else "FAIL","errors":errors,"checks":checks}
out = LAB / "artifacts" / ("pre-receipt-validation.json" if args.phase == "pre" else "final-validation.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"phase":args.phase,"status":result["status"],"errors":errors,"output":str(out),"activity_accounting":checks["activity_accounting"]}, indent=2, sort_keys=True))
raise SystemExit(0 if not errors else 1)
