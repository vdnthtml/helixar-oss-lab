#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import pathlib

LAB = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
DATA = VAULT / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O02-brain-memory"
REPORT = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O02 Brain, Memory, Retrieval and Storage OSS Lab Report.md"
processes = [json.loads(line) for line in (LAB / "process-log.jsonl").read_text().splitlines() if line.strip()]
by_seq = {row["sequence"]: row for row in processes}
network_count = len([line for line in (LAB / "network-fetch-log.jsonl").read_text().splitlines() if line.strip()])
fingerprints = json.loads((LAB / "artifacts/fixture-and-environment-fingerprints.json").read_text())
fixture_sha = {pathlib.Path(row["path"]).name: row["sha256"] for row in fingerprints["fixtures"]}
freeze_sha = {name: row["sha256"] for name, row in fingerprints["environment_freezes"].items()}


def read_csv(name: str):
    path = DATA / name
    with path.open(newline="", encoding="utf-8") as handle:
        return path, list(csv.DictReader(handle))


def write_csv(path: pathlib.Path, rows: list[dict]):
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ev(seq: int) -> str:
    row = by_seq[seq]
    return f"sequence {seq}; {row['stdout_path']} sha256={row['stdout_sha256']}; {row['stderr_path']} sha256={row['stderr_sha256']}"

# Candidate inventory: preserve intermittent current-fixture failure.
path, rows = read_csv("candidate-inventory.csv")
for row in rows:
    if row["candidate_id"] == "MEM0":
        row["deterministic_fixture_passed"] = "partial/flaky"
        row["integration_fit_proven"] = "partial"
        row["relevance"] = "CRUD/history/deletion/lineage are useful behind Helixar governance; embedded-Qdrant concurrent writes are flaky."
        row["proof_boundary"] = "Current fingerprinted fixture repeated three times: two full passes and one PARTIAL_CONCURRENCY_FAIL with 7/8 successful API returns but 8 persisted rows; earlier SQLite failures remain evidence."
write_csv(path, rows)

# Deployment matrix: preserve old rows and append fingerprinted reruns.
path, rows = read_csv("deployment-smoke-results.csv")
for row in rows:
    row.setdefault("fixture_sha256", "")
    row.setdefault("environment_freeze_sha256", "")
    if row["test_id"] == "MEM0-FINAL":
        row["status"] = "PASS_SINGLE_RUN_SUPERSEDED"
        row["limitations"] += " Superseded by fingerprinted repeats 75-77, one of which returned PARTIAL_CONCURRENCY_FAIL."
        row["fixture_sha256"] = fixture_sha["mem0_fixture.py"]
        row["environment_freeze_sha256"] = freeze_sha["mem0"]
    if row["test_id"] == "GRAPHITI-KUZU":
        row["status"] = "PASS_BOUNDED_CRUD"
        row["fixture_sha256"] = fixture_sha["graphiti_kuzu_fixture.py"]
        row["environment_freeze_sha256"] = freeze_sha["graphiti"]
existing = {row["test_id"] for row in rows}
for test_id, seq, status, checks, limits in [
    ("MEM0-FINGERPRINTED-REPEAT-1",75,"PASS","8/8 API returns; 8 persisted; stable post-concurrency retrieval; governance, deletion, export and egress checks passed.","Current fixture version; does not erase earlier-variant failures."),
    ("MEM0-FINGERPRINTED-REPEAT-2",76,"FLAKY_PARTIAL","7/8 API returns; 8 persisted rows; post-concurrency retrieval stable; one OperationalError was recorded.","Process exited 0 because the fixture reports partial status in JSON; embedded local-Qdrant concurrency is flaky."),
    ("MEM0-FINGERPRINTED-REPEAT-3",77,"PASS","8/8 API returns; 8 persisted; stable post-concurrency retrieval; governance, deletion, export and egress checks passed.","Current fixture version; aggregate disposition remains FLAKY/PARTIAL because repeat 2 failed."),
    ("GRAPHITI-KUZU-FINGERPRINTED",78,"PASS_BOUNDED_CRUD","Entity save/get; source lineage; governance metadata update; group exclusion; JSON export/reload; hard deletion; zero external egress attempts.","Kuzu is deprecated; no episode extraction, temporal-edge search, production graph backend, LLM, concurrency, backup or production operations."),
]:
    if test_id in existing:
        continue
    p = by_seq[seq]
    rows.append({
        "test_id": test_id,
        "candidate_id": "MEM0" if test_id.startswith("MEM0") else "GRAPHITI",
        "component": "fingerprinted Mem0 embedded-Qdrant concurrency fixture" if test_id.startswith("MEM0") else "fingerprinted Graphiti local Kuzu CRUD fixture",
        "proof_level": "same-version bounded repeat" if test_id.startswith("MEM0") else "bounded graph-storage fixture",
        "status": status,
        "command": p["shell"],
        "exit_code": p["exit_code"],
        "duration_seconds": p["duration_seconds"],
        "stdout_path": p["stdout_path"],
        "stdout_sha256": p["stdout_sha256"],
        "stderr_path": p["stderr_path"],
        "stderr_sha256": p["stderr_sha256"],
        "checks_passed": checks,
        "limitations": limits,
        "fixture_sha256": fixture_sha["mem0_fixture.py"] if test_id.startswith("MEM0") else fixture_sha["graphiti_kuzu_fixture.py"],
        "environment_freeze_sha256": freeze_sha["mem0"] if test_id.startswith("MEM0") else freeze_sha["graphiti"],
    })
write_csv(path, rows)
smoke_row_count = len(rows)

# Contract fit: rebuild the complete eight-candidate matrix to repair a malformed concurrent CSV row safely.
path = DATA / "contract-fit.csv"
rows = [
    {"candidate_id":"LETTA","capability":"working state/memory classes","native_support":"yes conceptually","fixture_proof":"none","fit_status":"ADAPT_CONCEPTS_ONLY","wrapper_required":"Helixar promotion/revocation, approval, concurrency and source-lineage authority","risk":"Legacy repo deprecated; successor/runtime contract changed.","evidence":"R01-O009; repos/letta/README.md:8-25"},
    {"candidate_id":"MEM0","capability":"scoped CRUD/search/history/delete","native_support":"yes","fixture_proof":"FLAKY/PARTIAL: current fingerprinted fixture passed 2/3; one run had 7/8 API returns with 8 persisted rows","fit_status":"ADAPT_WITH_SERIALIZED_OR_SERVER_WRITER_POC","wrapper_required":"proposal/approval/revocation state machine; immutable audit; CAS/idempotency; stable-ID tie-break and bounded score tolerance","risk":"Embedded local-Qdrant concurrency is intermittent; successful persistence despite an API error complicates retry/idempotency; scores are not bit-exact; telemetry defaults on.","evidence":"; ".join(ev(seq) for seq in [75,76,77])},
    {"candidate_id":"GRAPHITI","capability":"bitemporal facts, episodes and provenance","native_support":"yes by source/docs","fixture_proof":"bounded graph-storage CRUD PASS","fit_status":"POC_MORE","wrapper_required":"canonical proposal/approval; temporal query projection; production backend; immutable audit; concurrency and backup","risk":"Deprecated Kuzu adapter only; no episode extraction, temporal-edge search, Neo4j/FalkorDB or LLM; metadata update is not canonical revocation.","evidence":ev(78)+"; repos/graphiti/README.md:42-49,65-82,120-136,160-170"},
    {"candidate_id":"LLAMAINDEX","capability":"nodes, deterministic retrieval, persistence and adapters","native_support":"yes","fixture_proof":"PASS","fit_status":"ADAPT_BOUNDED_RETRIEVAL","wrapper_required":"governance state/audit; stable export schema; orchestration kept outside","risk":"Dependency/component churn and default hosted model resolution if local embedder omitted.","evidence":ev(32)+"; "+ev(48)},
    {"candidate_id":"UNSTRUCTURED","capability":"partition, metadata lineage and export","native_support":"yes","fixture_proof":"PASS on text/Markdown","fit_status":"ADAPT_AFTER_GOLDEN_CORPUS","wrapper_required":"source digest envelope; prompt-injection quarantine; memory governance outside parser","risk":"Heavy dependencies; format variance; optional runtime model download.","evidence":ev(33)+"; "+ev(50)},
    {"candidate_id":"PGVECTOR","capability":"ACID metadata + vector search","native_support":"yes by source","fixture_proof":"not run","fit_status":"ARCHITECTURE_CANDIDATE","wrapper_required":"tenant schema; append-only audit rules; migration/backup policy","risk":"Operational PostgreSQL ownership and index tuning unproven.","evidence":"repos/pgvector/README.md:1-34,53-128"},
    {"candidate_id":"QDRANT","capability":"payload-filtered vector retrieval","native_support":"yes","fixture_proof":"embedded adapter PASS","fit_status":"ADAPT_RETRIEVAL_INDEX","wrapper_required":"canonical truth remains PostgreSQL/object/audit layer; explicit tenant/filter contracts","risk":"Local mode lacks effective payload indexes; server quickstart insecure by default; HA/auth unproven.","evidence":ev(48)+"; repos/qdrant/README.md:44-62"},
    {"candidate_id":"MINIO","capability":"S3-compatible object storage","native_support":"yes by source","fixture_proof":"not run","fit_status":"REJECT_CODE_ADOPTION","wrapper_required":"content-addressed keys; retention; legal/licensing boundary","risk":"AGPL-3.0; repository unmaintained/source-only; commercial successor not source-equivalent.","evidence":"repos/minio/README.md:1-7,26-47,166-170"},
]
write_csv(path, rows)

# Correct security notes after sanitized environment checks.
path, rows = read_csv("license-and-security.csv")
for row in rows:
    if row["candidate_id"] in {"MEM0","GRAPHITI","LLAMAINDEX","UNSTRUCTURED"}:
        row["security_notes"] = row["security_notes"].replace("pip check is blocked by unrelated hermes-agent venv contamination.", "Initial pip check was contaminated by inherited PYTHONPATH; sanitized checks passed for all four isolated venvs (sequence 73).")
        if "sequence 73" not in row["evidence"]:
            row["evidence"] += "; " + ev(73)
write_csv(path, rows)

# Report reconciliation. Exact anchors intentionally fail if a sibling changed the file.
text = REPORT.read_text(encoding="utf-8")
repls = {
"status: validated-bounded-pass-with-disclosed-gaps":"status: final-gate-pending",
"**Mem0 is `ADAPT`, not autonomous truth.** Its scoped CRUD, history, deletion tombstone, persistence, eight concurrent writes, stable ordered IDs, governance wrapper and export/reload passed in the final bounded fixture. Raw similarity scores were not bit-exact (maximum drift `1.7947999975120865e-08`) and earlier runs exposed one local-Qdrant SQLite concurrency failure. Use only behind idempotency/CAS, stable-ID tie-break, bounded score tolerance and an independent immutable governance audit; server-backed concurrency remains unproven.":"**Mem0 is `ADAPT`, not autonomous truth, and its embedded local-Qdrant concurrency is `FLAKY/PARTIAL`.** The current fingerprinted fixture was run three times: two full passes and one `PARTIAL_CONCURRENCY_FAIL`. The partial run returned 7/8 successful API results while all 8 rows persisted, with `OperationalError: cannot commit - no transaction is active`; post-concurrency reads remained stable. This ambiguous retry outcome requires a serialized or server-backed writer POC, idempotency/CAS, stable-ID tie-break, bounded score tolerance and independent immutable governance audit.",
"| Mem0 | PASS | PASS | N/A library | PASS with bounded float tolerance | Partial behind wrapper | Unknown |":"| Mem0 | PASS | PASS | N/A library | FLAKY/PARTIAL (2/3 current repeats passed) | Partial behind wrapper | Unknown |",
"- Mem0 final bounded fixture: `sequence 64; /Users/vedantswami/Projects/helixar-oss-labs/O02-brain-memory/logs/064-mem0-fixture-final-partial-concurrency.stdout.log sha256=a080aaec9fa4b481f3ac19b5f52e4a3291e54389d30368ea8e159d02810230c0; /Users/vedantswami/Projects/helixar-oss-labs/O02-brain-memory/logs/064-mem0-fixture-final-partial-concurrency.stderr.log sha256=91e7bad7512e3eff88697fc1a7fedf285f52ea2df0a1a052e9c5521a742c11a8`. It passed eight concurrent writes, exact ordered IDs across five repetitions, bounded score tolerance, governance filtering, deletion/tombstone history, export/reload and the egress guard.":"- Mem0 single final fixture at sequence 64 passed, but is superseded by the fingerprinted repeated probe below.",
"- Mem0 falsification history remains evidence, not hidden: `sequence 38` captured one embedded-Qdrant SQLite concurrency failure; sequences `52`, `54` and `56` exposed that raw floating-point scores can alternate between `1.0` and `0.999999982052` even when IDs and order are unchanged. The final oracle correctly treats stable ordered IDs as authoritative and records the score tolerance rather than claiming bit-exact floats.":f"- Mem0 fingerprinted repeated probe: `{ev(75)}` PASS; `{ev(76)}` `FLAKY_PARTIAL` with 7/8 successful API returns but 8 persisted rows; `{ev(77)}` PASS. Fixture SHA-256 `{fixture_sha['mem0_fixture.py']}` and environment-freeze SHA-256 `{freeze_sha['mem0']}` were constant across repeats. Earlier variant failures at sequences 38/52/54/56 remain evidence; they are not relabeled as same-version flakiness because their historical fixture hashes were not captured.",
"- Graphiti bounded Kuzu CRUD fixture: `sequence 71; /Users/vedantswami/Projects/helixar-oss-labs/O02-brain-memory/logs/071-graphiti-kuzu-bounded-crud-fixture.stdout.log sha256=9f5389b371667ca53ca409c574bac342f9bd89df77304f6fc072101b7889cded; /Users/vedantswami/Projects/helixar-oss-labs/O02-brain-memory/logs/071-graphiti-kuzu-bounded-crud-fixture.stderr.log sha256=9db260688ec2c52712202eeb21f50fad3da869ca25bd30fd1ba058e30089a8d0`. Graph storage CRUD, source lineage, governance metadata, group exclusion, export/reload, hard deletion and zero external egress attempts passed; Kuzu deprecation and missing temporal/LLM paths are explicit.":f"- Graphiti fingerprinted bounded Kuzu CRUD fixture: `{ev(78)}`. Fixture SHA-256 `{fixture_sha['graphiti_kuzu_fixture.py']}`; environment-freeze SHA-256 `{freeze_sha['graphiti']}`. Graph storage CRUD, source lineage, governance metadata, group exclusion, export/reload, hard deletion and zero external egress attempts passed; Kuzu deprecation and missing temporal/LLM paths are explicit.",
"- Final `pip check` is blocked by an unrelated `hermes-agent 0.16.0` package present in every candidate venv; its missing/pinned requirements—not the exercised candidate packages—produce the reported conflicts. Removal was not performed because the destructive command required user confirmation. Environment dependency integrity is therefore `BLOCKED_CONTAMINATION`, not a clean PASS.":f"- Initial `pip check` output was contaminated by inherited `PYTHONPATH`, which exposed the host Hermes editable distribution. The venvs all declare `include-system-site-packages = false`; after removing inherited Python environment variables, all four candidate environments passed `pip check`: `{ev(73)}`. No package removal was needed.",
"- Recorded public-network command envelopes at finalization: **26**.":f"- Recorded public-network command envelopes before receipt/final gate: **{network_count}**.",
"O02 did not overwrite or roll back those sibling additions. Therefore the strict original 30-file manifest gate is **BLOCKED_CONCURRENT_DRIFT**, while the immutable inventory/evidence source-CSV gate is **PASS**. A post-write check must prove O02 did not alter the frozen CSV corpus.":"O02 did not overwrite or roll back those sibling additions. Therefore the strict original 30-file manifest gate is **BLOCKED_CONCURRENT_DRIFT**, while the immutable inventory/evidence source-CSV gate is **PASS**. The detached final-validation manifest performs the post-receipt source-CSV recheck.",
"| Dated run receipt | PASS |":"| Dated run receipt | PENDING FINALIZATION |",
"| Memory/retrieval smoke minimum | PASS_BOUNDED: independent Mem0, LlamaIndex and Graphiti graph-CRUD fixtures; embedded Qdrant also passed through the combination fixture |":"| Memory/retrieval smoke minimum | PASS_BOUNDED: LlamaIndex, Unstructured and Graphiti bounded fixtures passed; Mem0 remains FLAKY/PARTIAL; embedded Qdrant passed through the combination fixture |",
"| Candidate environment dependency consistency | BLOCKED_CONTAMINATION: unrelated `hermes-agent` package prevents clean `pip check` |":"| Candidate environment dependency consistency | PASS: sanitized `pip check` passed in all four isolated venvs (sequence 73) |",
}
for old, new in repls.items():
    if old not in text:
        raise RuntimeError(f"report anchor missing: {old[:120]!r}")
    text = text.replace(old, new, 1)
REPORT.write_text(text, encoding="utf-8")
print(json.dumps({
    "candidate_rows": 8,
    "smoke_rows": smoke_row_count,
    "report": str(REPORT),
    "network_envelopes_before_final_gate": network_count,
    "mem0_fixture_sha256": fixture_sha["mem0_fixture.py"],
    "graphiti_fixture_sha256": fixture_sha["graphiti_kuzu_fixture.py"],
}, indent=2, sort_keys=True))
