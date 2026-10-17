#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import splink.comparison_library as cl
from splink import DuckDBAPI, Linker, SettingsCreator, block_on

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "splink"
OUT.mkdir(parents=True, exist_ok=True)
RECORDS = [
    {"record_id": "r1", "name": "Acme Signal", "domain": "acme.invalid"},
    {"record_id": "r2", "name": "ACME Signal", "domain": "acme.invalid"},
    {"record_id": "r3", "name": "Acme Systems", "domain": "systems.invalid"},
    {"record_id": "r4", "name": "Beta Labs", "domain": "beta.invalid"},
]
SETTINGS = SettingsCreator(
    link_type="dedupe_only",
    unique_id_column_name="record_id",
    probability_two_random_records_match=0.05,
    comparisons=[
        cl.ExactMatch("domain").configure(
            m_probabilities=[0.98, 0.02],
            u_probabilities=[0.02, 0.98],
        ),
        cl.JaroWinklerAtThresholds("name", [0.95, 0.80]).configure(
            m_probabilities=[0.70, 0.20, 0.08, 0.02],
            u_probabilities=[0.01, 0.03, 0.10, 0.86],
        ),
    ],
    blocking_rules_to_generate_predictions=[block_on("domain")],
    retain_matching_columns=True,
    retain_intermediate_calculation_columns=True,
)


def run_once() -> list[dict]:
    db_api = DuckDBAPI()
    input_table = db_api.register(RECORDS, table_name="synthetic_entities")
    linker = Linker(input_table, SETTINGS, log_level=None)
    rows = linker.inference.predict(threshold_match_weight=-100).as_record_list()
    wanted = []
    for row in rows:
        wanted.append({
            "record_id_l": row["record_id_l"],
            "record_id_r": row["record_id_r"],
            "match_weight": round(float(row["match_weight"]), 10),
            "match_probability": round(float(row["match_probability"]), 10),
        })
    return sorted(wanted, key=lambda x: (x["record_id_l"], x["record_id_r"]))


a = run_once()
b = run_once()
canon = json.dumps(a, sort_keys=True, separators=(",", ":"))
assertions = {
    "repeat_equal": a == b,
    "only_blocked_pair_returned": [(r["record_id_l"], r["record_id_r"]) for r in a] == [("r1", "r2")],
    "candidate_probability_above_half": len(a) == 1 and a[0]["match_probability"] > 0.5,
    "input_records_unchanged": RECORDS[0]["record_id"] == "r1" and len(RECORDS) == 4,
}
summary = {
    "candidate": "Splink",
    "version": "5.0.0.dev4-source-commit-4774c889141ddff0b7a80fd3a1dbeaf6699419c0",
    "pairs": a,
    "output_sha256": hashlib.sha256(canon.encode()).hexdigest(),
    "assertions": assertions,
    "pass": all(assertions.values()),
    "authority_boundary": "Candidate pair only; no source record merge or external write.",
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary["pass"] else 2)
