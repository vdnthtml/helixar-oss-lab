#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent
OPA = LAB / "envs/opa/opa"
CEDAR = LAB / "envs/cedar-poc/bin/cedar"
GEN = ROOT / "generated"
GEN.mkdir(exist_ok=True)


def run(argv: list[str]) -> dict:
    t0 = time.perf_counter()
    p = subprocess.run(argv, cwd=LAB, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {
        "argv": [str(x) for x in argv],
        "exit_code": p.returncode,
        "output": p.stdout.strip(),
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 3),
    }


def paths_for(case: dict) -> tuple[Path, Path, Path]:
    case_dir = GEN / case["id"]
    case_dir.mkdir(exist_ok=True)
    input_doc = {
        "subject": {"tenant": case["subject_tenant"]},
        "action": case["action"],
        "resource": {
            "tenant": case["resource_tenant"],
            "target_hash": case["resource_target_hash"],
        },
        "approval": {
            "valid": case["approval_valid"],
            "revoked": case["approval_revoked"],
            "target_hash": case["approval_target_hash"],
        },
    }
    entities = [
        {
            "uid": {"type": "Helixar::Operator", "id": "operator.invalid"},
            "attrs": {"tenant": case["subject_tenant"]},
            "parents": [],
        },
        {
            "uid": {"type": "Helixar::Proposal", "id": "proposal.invalid"},
            "attrs": {
                "tenant": case["resource_tenant"],
                "targetHash": case["resource_target_hash"],
            },
            "parents": [],
        },
    ]
    context = {
        "approvalValid": case["approval_valid"],
        "approvalRevoked": case["approval_revoked"],
        "approvalTargetHash": case["approval_target_hash"],
    }
    input_path = case_dir / "opa-input.json"
    entities_path = case_dir / "cedar-entities.json"
    context_path = case_dir / "cedar-context.json"
    input_path.write_text(json.dumps(input_doc, indent=2) + "\n")
    entities_path.write_text(json.dumps(entities, indent=2) + "\n")
    context_path.write_text(json.dumps(context, indent=2) + "\n")
    return input_path, entities_path, context_path


def opa_command(input_path: Path) -> list[str]:
    return [
        str(OPA), "eval", "--strict", "--strict-builtin-errors", "--format", "raw",
        "--data", str(ROOT / "opa/policy.rego"),
        "--input", str(input_path),
        "--schema", str(ROOT / "opa/input-schema.json"),
        "data.helixar.authz.allow",
    ]


def cedar_command(action: str, entities_path: Path, context_path: Path, verbose: bool = False) -> list[str]:
    cmd = [
        str(CEDAR), "authorize",
        "--schema", str(ROOT / "cedar/schema.cedarschema"),
        "--policies", str(ROOT / "cedar/policy.cedar"),
        "--entities", str(entities_path),
        "--context", str(context_path),
        "--principal", 'Helixar::Operator::"operator.invalid"',
        "--action", f'Helixar::Action::"{action}"',
        "--resource", 'Helixar::Proposal::"proposal.invalid"',
        "--error-format", "plain",
    ]
    if verbose:
        cmd.append("--verbose")
    return cmd


cases = json.loads((ROOT / "cases.json").read_text())["cases"]
results: list[dict] = []
case_paths: dict[str, tuple[Path, Path, Path]] = {}
for case in cases:
    input_path, entities_path, context_path = paths_for(case)
    case_paths[case["id"]] = (input_path, entities_path, context_path)
    opa = run(opa_command(input_path))
    cedar = run(cedar_command(case["action"], entities_path, context_path, verbose=True))
    opa_decision = "ALLOW" if opa["exit_code"] == 0 and opa["output"].splitlines()[-1:] == ["true"] else "DENY" if opa["exit_code"] == 0 else "ERROR"
    cedar_lines = [line.strip() for line in cedar["output"].splitlines()]
    cedar_decision = next((line for line in cedar_lines if line in {"ALLOW", "DENY"}), "ERROR")
    matched = opa_decision == cedar_decision == case["expected"]
    results.append({
        "case_id": case["id"], "expected": case["expected"],
        "opa_decision": opa_decision, "cedar_decision": cedar_decision,
        "matched": matched, "opa": opa, "cedar": cedar,
    })

# Static typo checks: both must reject before deployment with schema-aware validation.
static_checks = {
    "opa_valid": run([str(OPA), "check", "--strict", "--schema", str(ROOT / "opa/input-schema.json"), str(ROOT / "opa/policy.rego")]),
    "opa_typo": run([str(OPA), "check", "--strict", "--schema", str(ROOT / "opa/input-schema.json"), str(ROOT / "opa/policy-typo.rego")]),
    "cedar_valid": run([str(CEDAR), "validate", "--schema", str(ROOT / "cedar/schema.cedarschema"), "--policies", str(ROOT / "cedar/policy.cedar"), "--error-format", "plain"]),
    "cedar_typo": run([str(CEDAR), "validate", "--schema", str(ROOT / "cedar/schema.cedarschema"), "--policies", str(ROOT / "cedar/policy-typo.cedar"), "--error-format", "plain"]),
}

# Runtime malformed input behavior. OPA schema guides compilation but does not validate each input document.
base_case = dict(cases[0])
malformed: dict[str, dict] = {}
for fault in ("missing_revoked", "wrong_type"):
    case = dict(base_case)
    case["id"] = f"malformed_{fault}"
    input_path, entities_path, context_path = paths_for(case)
    input_doc = json.loads(input_path.read_text())
    context_doc = json.loads(context_path.read_text())
    if fault == "missing_revoked":
        del input_doc["approval"]["revoked"]
        del context_doc["approvalRevoked"]
    else:
        input_doc["approval"]["valid"] = "true"
        context_doc["approvalValid"] = "true"
    input_path.write_text(json.dumps(input_doc, indent=2) + "\n")
    context_path.write_text(json.dumps(context_doc, indent=2) + "\n")
    malformed[fault] = {
        "opa": run(opa_command(input_path)),
        "cedar": run(cedar_command(case["action"], entities_path, context_path)),
    }

# CLI wall-time benchmark. This includes process startup and parsing, not only evaluator time.
bench_case = case_paths["allow_exact_scope"]
bench: dict[str, dict] = {}
for name, command in {
    "opa": opa_command(bench_case[0]),
    "cedar": cedar_command("propose", bench_case[1], bench_case[2]),
}.items():
    samples = []
    for _ in range(50):
        r = run(command)
        if r["exit_code"] != 0:
            raise SystemExit(f"benchmark command failed for {name}: {r['output']}")
        samples.append(r["elapsed_ms"])
    ordered = sorted(samples)
    bench[name] = {
        "iterations": len(samples),
        "median_ms": round(statistics.median(samples), 3),
        "p95_ms": round(ordered[int(len(ordered) * 0.95) - 1], 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
    }

acceptance = {
    "six_case_parity": all(r["matched"] for r in results) and len(results) == 6,
    "opa_valid_policy_passes": static_checks["opa_valid"]["exit_code"] == 0,
    "cedar_valid_policy_passes": static_checks["cedar_valid"]["exit_code"] == 0,
    "opa_typo_rejected": static_checks["opa_typo"]["exit_code"] != 0,
    "cedar_typo_rejected": static_checks["cedar_typo"]["exit_code"] != 0,
    "malformed_fail_closed": all(
        ("false" in value["opa"]["output"].lower() or value["opa"]["exit_code"] != 0)
        and ("deny" in value["cedar"]["output"].lower() or value["cedar"]["exit_code"] != 0)
        for value in malformed.values()
    ),
}
summary = {
    "status": "PASS" if all(acceptance.values()) else "FAIL",
    "acceptance": acceptance,
    "cases": results,
    "static_checks": static_checks,
    "malformed": malformed,
    "benchmark": bench,
    "benchmark_scope": "50 sequential CLI process invocations; includes startup/parsing; not evaluator-only throughput",
}
(ROOT / "comparison-results.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
with (ROOT / "comparison-results.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["case_id", "expected", "opa_decision", "cedar_decision", "matched", "opa_ms", "cedar_ms"])
    writer.writeheader()
    for row in results:
        writer.writerow({
            "case_id": row["case_id"], "expected": row["expected"],
            "opa_decision": row["opa_decision"], "cedar_decision": row["cedar_decision"],
            "matched": row["matched"], "opa_ms": row["opa"]["elapsed_ms"], "cedar_ms": row["cedar"]["elapsed_ms"],
        })
print(json.dumps({"status": summary["status"], "acceptance": acceptance, "benchmark": bench}, indent=2))
raise SystemExit(0 if summary["status"] == "PASS" else 1)
