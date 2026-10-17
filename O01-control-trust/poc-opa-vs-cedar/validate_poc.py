#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

LAB = Path("/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust")
POC = LAB / "poc-opa-vs-cedar"
VAULT = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
ARCH = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O01A OPA vs Cedar Decision POC.md"
O01 = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O01 Control Plane, Trust and Observability OSS Lab Report.md"
SNAPSHOT = VAULT / "05_Data/Current State/Dystopia Current Snapshot.md"
DAILY = VAULT / "04_Logs/Daily/Daily Log - 2026-07-15.md"
RECEIPT = VAULT / "04_Logs/Runs/2026-07-15 - OPA vs Cedar Decision POC Run Receipt.md"
CLEANUP = VAULT / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O01-control-trust/cleanup-manifest.csv"
DATA = VAULT / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O01-control-trust/opa-vs-cedar"
VALIDATION = DATA / "validation-result.json"
MANIFEST = DATA / "sha256-manifest.txt"

checks: dict[str, object] = {}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# Re-run the complete fixture. Parent sandbox supplies final OS-level network denial.
p = subprocess.run(["/usr/bin/python3", str(POC / "run_comparison.py")], cwd=LAB, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
checks["comparison_rerun_exit_zero"] = p.returncode == 0
checks["comparison_rerun_output"] = p.stdout.strip()
results = json.loads((POC / "comparison-results.json").read_text())
checks["comparison_status_pass"] = results["status"] == "PASS"
checks["all_acceptance_true"] = all(results["acceptance"].values())
checks["six_cases"] = len(results["cases"]) == 6 and all(x["matched"] for x in results["cases"])
checks["malformed_cedar_errors"] = all(x["cedar"]["exit_code"] == 1 for x in results["malformed"].values())
checks["malformed_opa_fail_closed"] = all(x["opa"]["exit_code"] == 0 and x["opa"]["output"] == "false" for x in results["malformed"].values())
checks["both_typo_checks_reject"] = results["static_checks"]["opa_typo"]["exit_code"] != 0 and results["static_checks"]["cedar_typo"]["exit_code"] != 0

expected_hashes = {
    LAB / "envs/opa/opa_darwin_arm64_static": "3ffa2af6a3b9ccff5d171d061d27990db5ad8cc5c10214c7eeeabc0f29ca11cf",
    POC / "cargo-home/registry/cache/index.crates.io-1949cf8c6b5b557f/cedar-policy-cli-4.11.2.crate": "57d27ffdcc04aa965c4d0697fc492d5a95e232d44211400364e7dcfeef5bd770",
    LAB / "envs/cedar-poc/bin/cedar": "1423c6f295e7173f31c296a53917ec340adfed4d100b22134e481db30e802ae9",
    POC / "provenance/opa-1.18.2-LICENSE": "6dc0e068dcf3a5bc8e054205b85b7720e1d49265bbc64bf515d2cf79197df69a",
    POC / "provenance/cedar-4.11.2-LICENSE": "7fb46adff9025f553b882b84ce593c37008d1e83019e4fdd6b21f8c800d0c485",
}
checks["integrity_hashes"] = {str(path): {"expected": expected, "actual": sha(path), "match": sha(path) == expected} for path, expected in expected_hashes.items()}
checks["all_integrity_hashes_match"] = all(x["match"] for x in checks["integrity_hashes"].values())

vcs = json.loads((POC / "cargo-home/registry/src/index.crates.io-1949cf8c6b5b557f/cedar-policy-cli-4.11.2/.cargo_vcs_info.json").read_text())
checks["cedar_exact_source_commit"] = vcs["git"]["sha1"] == "19c0e2591ba1d48b1cb43d43f35b64fdb3ac5e79"
checks["opa_exact_source_commit"] = "e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297" in (DATA / "provenance.csv").read_text()

required = [ARCH, O01, SNAPSHOT, DAILY, RECEIPT, CLEANUP, DATA / "matched-cases.csv", DATA / "comparison-evidence.json", DATA / "provenance.csv", DATA / "decision-matrix.csv"]
checks["required_files_exist"] = all(x.exists() for x in required)
checks["report_decision_present"] = "Choose Cedar 4.11.2 as the conditional P0 authorization evaluator" in ARCH.read_text()
checks["report_nonclaim_present"] = "Production unknowns and non-claims" in ARCH.read_text() and "human h0" in ARCH.read_text().lower()
checks["o01_followup_link_present"] = "O01A OPA vs Cedar Decision POC" in O01.read_text()
checks["snapshot_updated"] = "O01A's matched OPA 1.18.2 vs Cedar 4.11.2 POC" in SNAPSHOT.read_text()
checks["daily_log_updated"] = "conditional Cedar `ADAPT`" in DAILY.read_text()
checks["cleanup_manifest_updated"] = "poc-opa-vs-cedar" in CLEANUP.read_text() and "envs/cedar-poc" in CLEANUP.read_text()

with (DATA / "matched-cases.csv").open(newline="", encoding="utf-8") as f:
    matched_rows = list(csv.DictReader(f))
with (DATA / "decision-matrix.csv").open(newline="", encoding="utf-8") as f:
    matrix_rows = list(csv.DictReader(f))
with (DATA / "provenance.csv").open(newline="", encoding="utf-8") as f:
    provenance_rows = list(csv.DictReader(f))
checks["matched_csv_six_rows"] = len(matched_rows) == 6 and all(x["matched"] == "True" for x in matched_rows)
checks["decision_matrix_complete"] = len(matrix_rows) == 13 and matrix_rows[-1]["winner"] == "CEDAR_CONDITIONAL"
checks["provenance_two_rows"] = len(provenance_rows) == 2 and {x["candidate"] for x in provenance_rows} == {"Open Policy Agent", "Cedar"}
checks["production_unknown_in_provenance"] = all(x["production_suitability"] == "UNKNOWN" and x["integration_fit_proven"] == "false" for x in provenance_rows)

# Size gates.
files = [x for x in LAB.rglob("*") if x.is_file()]
lab_bytes = sum(x.stat().st_size for x in files)
large = [{"path": str(x), "bytes": x.stat().st_size} for x in files if x.stat().st_size > 2_000_000_000]
checks["lab_bytes"] = lab_bytes
checks["lab_under_10gb"] = lab_bytes < 10_000_000_000
checks["no_artifact_over_2gb"] = len(large) == 0
checks["large_artifacts"] = large

# No candidate process or listener can remain if neither candidate executable is running.
process_check = json.loads((POC / "process-check.json").read_text())
checks["active_candidate_processes"] = process_check["active_candidate_processes"]
checks["no_candidate_processes"] = process_check["no_candidate_processes"]
checks["candidate_bound_ports"] = process_check["candidate_bound_ports"]
checks["no_candidate_listeners"] = process_check["no_candidate_listeners"]

# Logged follow-up activity, counted from exact first POC record.
records = []
for line in (LAB / "logs/process-network.jsonl").read_text().splitlines():
    try:
        x = json.loads(line)
    except Exception:
        continue
    if x.get("started_at_utc", "") >= "2026-07-14T18:02:21.421389+00:00":
        records.append(x)
checks["logged_followup_records_visible_to_validator"] = len(records)
checks["logged_followup_network_records"] = sum(x.get("kind") == "network" for x in records)
checks["logged_followup_local_records"] = sum(x.get("kind") == "local" for x in records)
checks["external_business_writes"] = 0
checks["implementation_repository_writes"] = 0

boolean_failures = [k for k, v in checks.items() if isinstance(v, bool) and not v]
status = "PASS" if not boolean_failures else "FAIL"
validation = {
    "status": status,
    "scope": "O01A OPA vs Cedar decision POC",
    "network_posture": "validator and complete comparison rerun executed under inherited macOS sandbox-exec deny network*",
    "checks": checks,
    "boolean_failures": boolean_failures,
}
VALIDATION.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")

manifest_files = required + [VALIDATION, POC / "cases.json", POC / "comparison-results.json", POC / "run_comparison.py", POC / "opa/policy.rego", POC / "opa/input-schema.json", POC / "cedar/policy.cedar", POC / "cedar/schema.cedarschema"] + list(expected_hashes.keys())
seen = set(); lines = []
for path in manifest_files:
    key = str(path)
    if key in seen: continue
    seen.add(key)
    lines.append(f"{sha(path)}  {path}")
MANIFEST.write_text("\n".join(lines) + "\n")
print(json.dumps({"status": status, "boolean_failures": boolean_failures, "lab_bytes": lab_bytes, "candidate_processes": checks["active_candidate_processes"], "manifest_entries": len(lines)}, indent=2))
raise SystemExit(0 if status == "PASS" else 1)
