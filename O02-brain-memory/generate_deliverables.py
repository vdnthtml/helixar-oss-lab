#!/usr/bin/env python3
"""Generate O02 Dystopia deliverables from retained lab evidence."""
from __future__ import annotations

import csv
import json
import pathlib
import re
from collections import Counter

LAB = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
REPORT = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O02 Brain, Memory, Retrieval and Storage OSS Lab Report.md"
DATA = VAULT / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O02-brain-memory"
DATA.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

manifest = {row["candidate"]: row for row in json.loads((LAB / "candidate-source-manifest.json").read_text())}
processes = [json.loads(line) for line in (LAB / "process-log.jsonl").read_text().splitlines() if line.strip()]
network = [json.loads(line) for line in (LAB / "network-fetch-log.jsonl").read_text().splitlines() if line.strip()]
by_seq = {row["sequence"]: row for row in processes}
source_manifest = json.loads((LAB / "source-hash-manifest.json").read_text())
source_verification = json.loads((LAB / "source-immutability-verification.json").read_text())
source_roles = {row["path"]: row["role"] for row in source_manifest}
source_csv_results = [row for row in source_verification["results"] if source_roles[row["path"]] == "source_csv"]
mandatory_drift = [row for row in source_verification["changed"] if source_roles.get(row["path"]) == "mandatory_context"]
fingerprints = json.loads((LAB / "artifacts/fixture-and-environment-fingerprints.json").read_text())
fixture_sha = {pathlib.Path(row["path"]).name: row["sha256"] for row in fingerprints["fixtures"]}
freeze_sha = {name: row["sha256"] for name, row in fingerprints["environment_freezes"].items()}


def evidence(seq: int) -> str:
    row = by_seq[seq]
    return f"sequence {seq}; {row['stdout_path']} sha256={row['stdout_sha256']}; {row['stderr_path']} sha256={row['stderr_sha256']}"


def write_csv(name: str, fields: list[str], rows: list[dict]) -> pathlib.Path:
    path = DATA / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    return path


candidates = [
    {
        "candidate_id": "LETTA", "candidate": "Letta", "assigned_or_added": "assigned", "source_asset_id": "R01-O009",
        "role": "stateful agent server and memory concepts", "primary_repository": manifest["Letta"]["repository_url"],
        "successor_repository": manifest["Letta current (letta-code)"]["repository_url"], "exact_commit": manifest["Letta"]["commit"],
        "successor_commit": manifest["Letta current (letta-code)"]["commit"], "tree_hash": manifest["Letta"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "false", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "false", "integration_fit_proven": "false", "production_suitability_unknown": "true",
        "classification": "REJECT_FIT", "relevance": "Memory concepts are useful, but the assigned server is legacy and the active successor is a full self-modifying agent harness that overlaps the proposed Helixar Agent OS authority boundary.",
        "proof_boundary": "Legacy and successor source inspected; no Node/LLM/local agent runtime executed. Rejection is for direct platform adoption, not for studying memory patterns.",
    },
    {
        "candidate_id": "MEM0", "candidate": "Mem0", "assigned_or_added": "assigned", "source_asset_id": "R01-O011",
        "role": "scoped memory SDK with embedded Qdrant and SQLite history", "primary_repository": manifest["Mem0"]["repository_url"],
        "successor_repository": "", "exact_commit": manifest["Mem0"]["commit"], "successor_commit": "", "tree_hash": manifest["Mem0"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "true", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "partial/flaky", "integration_fit_proven": "partial", "production_suitability_unknown": "true",
        "classification": "ADAPT", "relevance": "CRUD/history/deletion/lineage are useful behind Helixar governance; embedded-Qdrant concurrent writes are flaky.",
        "proof_boundary": "The current fingerprinted fixture passed 2/3 repeated runs. One run returned 7/8 successful API results while all 8 rows persisted; exact ordered IDs remained stable and score drift stayed within 1e-06. Serialized or server-backed writer behavior remains unproven.",
    },
    {
        "candidate_id": "GRAPHITI", "candidate": "Graphiti", "assigned_or_added": "assigned", "source_asset_id": "R01-O013",
        "role": "temporal context graph and provenance", "primary_repository": manifest["Graphiti"]["repository_url"],
        "successor_repository": "", "exact_commit": manifest["Graphiti"]["commit"], "successor_commit": "", "tree_hash": manifest["Graphiti"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "true", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "true (bounded Kuzu CRUD only)", "integration_fit_proven": "partial", "production_suitability_unknown": "true",
        "classification": "POC_MORE", "relevance": "Strong bitemporal/provenance model if flat retrieval later fails.",
        "proof_boundary": "Entity CRUD, lineage metadata, group isolation, export/reload and hard deletion passed on the deprecated Kuzu adapter; no episode extraction, temporal-edge search, supported production graph backend or structured-output LLM ran.",
    },
    {
        "candidate_id": "LLAMAINDEX", "candidate": "LlamaIndex", "assigned_or_added": "assigned", "source_asset_id": "R01-O014",
        "role": "document nodes, local retrieval, persistence and vector-store adapters", "primary_repository": manifest["LlamaIndex"]["repository_url"],
        "successor_repository": "", "exact_commit": manifest["LlamaIndex"]["commit"], "successor_commit": "", "tree_hash": manifest["LlamaIndex"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "true", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "true", "integration_fit_proven": "true (bounded retrieval role)", "production_suitability_unknown": "true",
        "classification": "ADAPT", "relevance": "Best tested retrieval abstraction; deterministic local embedding, source lineage, export/reload and explicit metadata governance all passed.",
        "proof_boundary": "Core and embedded Qdrant adapter only; no orchestration authority, server HA, auth, backup or hosted provider.",
    },
    {
        "candidate_id": "UNSTRUCTURED", "candidate": "Unstructured", "assigned_or_added": "assigned", "source_asset_id": "R01-O015",
        "role": "document partitioning and lineage transformation", "primary_repository": manifest["Unstructured"]["repository_url"],
        "successor_repository": "", "exact_commit": manifest["Unstructured"]["commit"], "successor_commit": "", "tree_hash": manifest["Unstructured"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "true", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "true", "integration_fit_proven": "true (text/Markdown ingestion only)", "production_suitability_unknown": "true",
        "classification": "ADAPT", "relevance": "Deterministic structural partitioning, metadata lineage and JSON round-trip passed.",
        "proof_boundary": "Tiny text/Markdown corpus only; OCR, tables, slides, spreadsheets and prompt-injection handling remain untested.",
    },
    {
        "candidate_id": "PGVECTOR", "candidate": "PostgreSQL+pgvector", "assigned_or_added": "added architecture", "source_asset_id": "",
        "role": "transactional relational plus vector persistence", "primary_repository": manifest["PostgreSQL+pgvector"]["repository_url"],
        "successor_repository": "", "exact_commit": manifest["PostgreSQL+pgvector"]["commit"], "successor_commit": "", "tree_hash": manifest["PostgreSQL+pgvector"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "false", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "false", "integration_fit_proven": "architecture only", "production_suitability_unknown": "true",
        "classification": "ADAPT", "relevance": "ACID, PITR, joins and vector search make it a strong canonical metadata/governance store candidate.",
        "proof_boundary": "Primary source inspected; no PostgreSQL server or extension installation ran in Wave A.",
    },
    {
        "candidate_id": "QDRANT", "candidate": "Qdrant", "assigned_or_added": "added architecture", "source_asset_id": "",
        "role": "vector retrieval store", "primary_repository": manifest["Qdrant"]["repository_url"],
        "successor_repository": "", "exact_commit": manifest["Qdrant"]["commit"], "successor_commit": "", "tree_hash": manifest["Qdrant"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "embedded qdrant-client only", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "true (embedded adapter)", "integration_fit_proven": "partial", "production_suitability_unknown": "true",
        "classification": "POC_MORE", "relevance": "Payload filtering and local persistence fit retrieval, but a dedicated server adds a second authority and is justified only by measured scale/recall triggers.",
        "proof_boundary": "Embedded qdrant-client passed with LlamaIndex and Mem0; Qdrant server/auth/replication/backup were not tested.",
    },
    {
        "candidate_id": "MINIO", "candidate": "MinIO", "assigned_or_added": "added architecture", "source_asset_id": "",
        "role": "S3-compatible immutable artifact/object storage", "primary_repository": manifest["MinIO"]["repository_url"],
        "successor_repository": "AIStor commercial/free distribution (not source-equivalent)", "exact_commit": manifest["MinIO"]["commit"], "successor_commit": "", "tree_hash": manifest["MinIO"]["tree_hash"],
        "source_inspected": "true", "install_attempted": "false", "service_or_cli_started": "false",
        "deterministic_fixture_passed": "false", "integration_fit_proven": "false", "production_suitability_unknown": "true",
        "classification": "REJECT_OPERATIONS", "relevance": "S3 interface is relevant, but this community source is unmaintained and source-only; AGPL-3.0 also requires counsel before any proprietary code use.",
        "proof_boundary": "No code adoption or runtime test; reject this implementation operationally and keep the S3-compatible interface open pending provider and legal decisions.",
    },
]

candidate_fields = list(candidates[0].keys())
write_csv("candidate-inventory.csv", candidate_fields, candidates)

license_rows = [
    {"candidate_id":"LETTA","repository":"repos/letta; repos/letta-code","commit":"b76da9092518cbaa2d09042e52fdcbde69243e18; 7d3afd54b930d092d5f4547b3d874cb7efb15999","license_file":"LICENSE; LICENSE","license_spdx":"Apache-2.0","license_sha256":"984c6db99fc6609803108dfc196762118662cd94b82a456dd9217583f18f3612; f755fe80260bbfde96447f9a352570378408e4e0decc6f4f916597991f7a6d7f","security_file":"legacy SECURITY.md; successor none found","telemetry_default":"successor enabled by default","telemetry_opt_out":"LETTA_CODE_TELEM=0","egress_endpoint":"PostHog/analytics endpoint configured in successor telemetry module; runtime not started","security_notes":"Legacy server deprecated. Successor tracks session activity and user-input telemetry paths unless disabled; full dependency/CVE scan not run because successor was not installed.","code_adoption_status":"REJECT_FIT","evidence":"repos/letta/AGENTS.md:3-18; repos/letta-code/src/index.ts:980-983; repos/letta-code/src/headless.ts:283-287; candidate-source-manifest.json"},
    {"candidate_id":"MEM0","repository":"repos/mem0","commit":manifest["Mem0"]["commit"],"license_file":"LICENSE","license_spdx":"Apache-2.0","license_sha256":"0bbcbe931c353293a2fafce08326181dfeea0e568c566afd4ce8337a70f5e219","security_file":"SECURITY.md","telemetry_default":"enabled","telemetry_opt_out":"MEM0_TELEMETRY=false before import","egress_endpoint":"https://us.i.posthog.com when enabled","security_notes":"PostHog is a core dependency. pip-audit found 7 known vulnerabilities only in pip/setuptools installer tooling and none on mem0ai itself. Sanitized pip check passed in the isolated venv.","code_adoption_status":"ADAPT_WITH_EGRESS_AND_GOVERNANCE_GUARDS","evidence":"repos/mem0/mem0/memory/telemetry.py:14-20,76-89; logs/066-pip-audit-mem0.stderr.log; " + evidence(73)},
    {"candidate_id":"GRAPHITI","repository":"repos/graphiti","commit":manifest["Graphiti"]["commit"],"license_file":"LICENSE","license_spdx":"Apache-2.0","license_sha256":"2825300b20d7b951209835a4a331f29e24725a39d65168e4b831df53aa372650","security_file":"SECURITY.md","telemetry_default":"enabled","telemetry_opt_out":"GRAPHITI_TELEMETRY_ENABLED=false","egress_endpoint":"https://us.i.posthog.com when enabled","security_notes":"Opt-out verified. pip-audit found 7 known vulnerabilities only in pip/setuptools installer tooling and none on graphiti-core. Sanitized pip check passed; Kuzu is deprecated because upstream is unmaintained.","code_adoption_status":"POC_MORE","evidence":"repos/graphiti/graphiti_core/telemetry/telemetry.py:15-37,40-60,76-114; logs/069-pip-audit-graphiti.stderr.log; " + evidence(73) + "; " + evidence(78)},
    {"candidate_id":"LLAMAINDEX","repository":"repos/llama_index","commit":manifest["LlamaIndex"]["commit"],"license_file":"LICENSE","license_spdx":"MIT","license_sha256":"24f40b5190fdacabc24ddbb5f76364d15e4f030925220ea300d8a2dd4993c8cb","security_file":"SECURITY.md","telemetry_default":"core instrumentation has no network exporter by default","telemetry_opt_out":"pass explicit local embedding/vector store; do not resolve hosted defaults","egress_endpoint":"none observed in tested path","security_notes":"Only llama-index-core and Qdrant adapter were used. pip-audit found 6 known vulnerabilities only in pip installer tooling and none on llama-index-core. Sanitized pip check passed.","code_adoption_status":"ADAPT_BOUNDED_CORE","evidence":"repos/llama_index/llama-index-core/pyproject.toml; logs/067-pip-audit-llamaindex.stderr.log; " + evidence(73) + "; " + evidence(48)},
    {"candidate_id":"UNSTRUCTURED","repository":"repos/unstructured","commit":manifest["Unstructured"]["commit"],"license_file":"LICENSE.md","license_spdx":"Apache-2.0","license_sha256":"4b190a3ffeb6b8800a6fd99bd5e1fb147e0a9f66984f4f5f8232a926de4fc939","security_file":"none found","telemetry_default":"opt-in/off by default","telemetry_opt_out":"DO_NOT_TRACK=1; SCARF_NO_ANALYTICS=1; UNSTRUCTURED_TELEMETRY_ENABLED=0","egress_endpoint":"https://packages.unstructured.io/python-telemetry only when explicitly enabled","security_notes":"Ordinary prose may trigger a pinned spaCy model download if absent. pip-audit found 7 known vulnerabilities only in pip/setuptools installer tooling and none on unstructured. Sanitized pip check passed; pin models before POC.","code_adoption_status":"ADAPT_AFTER_GOLDEN_CORPUS","evidence":"repos/unstructured/unstructured/utils.py:180-220; logs/068-pip-audit-unstructured.stderr.log; " + evidence(73) + "; " + evidence(50)},
    {"candidate_id":"PGVECTOR","repository":"repos/pgvector","commit":manifest["PostgreSQL+pgvector"]["commit"],"license_file":"LICENSE","license_spdx":"PostgreSQL","license_sha256":"6bba9ebeb73e27477463b05e5ef1bf303bccbddb3db9bbc95905d351604d6a87","security_file":"none found","telemetry_default":"none identified in extension source inspection","telemetry_opt_out":"not applicable/untested","egress_endpoint":"none identified","security_notes":"Production security is inherited from PostgreSQL deployment; extension supports PostgreSQL 13+.","code_adoption_status":"ARCHITECTURE_CANDIDATE","evidence":"repos/pgvector/README.md:1-34,53-128"},
    {"candidate_id":"QDRANT","repository":"repos/qdrant","commit":manifest["Qdrant"]["commit"],"license_file":"LICENSE","license_spdx":"Apache-2.0","license_sha256":"c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4","security_file":"none found at root","telemetry_default":"server enabled by default","telemetry_opt_out":"telemetry_disabled=true in Qdrant settings","egress_endpoint":"https://telemetry.qdrant.io when server telemetry is enabled; none in embedded fixture","security_notes":"README warns default container is insecure and exposed to all interfaces. Server deployment must bind loopback, configure auth, and disable telemetry before promotion.","code_adoption_status":"POC_MORE_SERVER; EMBEDDED_ADAPTER_PROVEN","evidence":"repos/qdrant/src/settings.rs:240-242; repos/qdrant/src/telemetry.rs:21-25; repos/qdrant/README.md:44-62; " + evidence(48)},
    {"candidate_id":"MINIO","repository":"repos/minio","commit":manifest["MinIO"]["commit"],"license_file":"LICENSE","license_spdx":"AGPL-3.0-only","license_sha256":"0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0","security_file":"SECURITY.md","telemetry_default":"runtime not tested; source exposes callhome/health reporting controls","telemetry_opt_out":"MINIO_CALLHOME_ENABLE=off/default per source; verify again for any commercial successor","egress_endpoint":"unknown in unstarted runtime","security_notes":"Community repository is unmaintained and source-only. Reject operationally; AGPL obligations separately require legal review for proprietary deployment.","code_adoption_status":"REJECT_OPERATIONS; LICENSE_REVIEW_REQUIRED","evidence":"repos/minio/README.md:1-7,26-47,92-94,166-170; repos/minio/cmd/callhome.go:29-31"},
]
write_csv("license-and-security.csv", list(license_rows[0].keys()), license_rows)

smoke_rows = []
def smoke(test_id,candidate_id,component,proof,status,seq,checks,limitations,fixture_sha256="",environment_freeze_sha256=""):
    row=by_seq[seq]
    smoke_rows.append({"test_id":test_id,"candidate_id":candidate_id,"component":component,"proof_level":proof,"status":status,"command":row["shell"],"exit_code":row["exit_code"],"duration_seconds":row["duration_seconds"],"stdout_path":row["stdout_path"],"stdout_sha256":row["stdout_sha256"],"stderr_path":row["stderr_path"],"stderr_sha256":row["stderr_sha256"],"checks_passed":checks,"limitations":limitations,"fixture_sha256":fixture_sha256,"environment_freeze_sha256":environment_freeze_sha256})
smoke("MEM0-INSTALL","MEM0","editable package install","install attempted","PASS",21,"Package and test dependencies installed in isolated venv.","Network lower-level request count unknown.")
smoke("MEM0-CORE","MEM0","Memory OSS + embedded Qdrant + SQLite","deterministic fixture subset","PASS",31,"Lineage; wrapper promotion/revocation; deletion tombstone; four concurrent writes; export; reopen persistence.","Warnings show spaCy/fastembed omitted; native revoked item remained retrievable without wrapper filter.")
smoke("MEM0-CONCURRENCY-HISTORICAL","MEM0","embedded Qdrant eight-write probe","fixture falsification","FAIL_VARIANT_UNFINGERPRINTED",38,"Failure captured at concurrent upsert.","sqlite3.OperationalError from an earlier fixture variant; retained as historical evidence rather than relabeled as same-version flakiness.")
smoke("MEM0-ORDER-HISTORICAL","MEM0","repeated retrieval order","fixture falsification","FAIL_VARIANT_UNFINGERPRINTED",54,"Earlier exact score/order assertion failed.","Historical fixture hash was not captured; final contract requires stable IDs/order and score drift <=1e-06 rather than bit-exact scores.")
smoke("MEM0-FINAL-SINGLE","MEM0","Memory OSS + isolated embedded Qdrant + SQLite history","single deterministic/concurrency fixture","PASS_SINGLE_RUN_SUPERSEDED",64,"CRUD; lineage; promotion/revocation wrapper; deletion; eight concurrent writes; five stable-order retrievals; persistence; export/reload; zero egress attempts.","Superseded by same-version fingerprinted repeats 75-77; aggregate disposition is FLAKY/PARTIAL.",fixture_sha["mem0_fixture.py"],freeze_sha["mem0"])
smoke("MEM0-FINGERPRINTED-REPEAT-1","MEM0","fingerprinted Mem0 embedded-Qdrant concurrency fixture","same-version bounded repeat","PASS",75,"8/8 API returns; 8 persisted; stable post-concurrency retrieval; governance, deletion, export and egress checks passed.","Current fixture version; aggregate disposition remains FLAKY/PARTIAL.",fixture_sha["mem0_fixture.py"],freeze_sha["mem0"])
smoke("MEM0-FINGERPRINTED-REPEAT-2","MEM0","fingerprinted Mem0 embedded-Qdrant concurrency fixture","same-version bounded repeat","FLAKY_PARTIAL",76,"7/8 API returns; 8 persisted rows; post-concurrency retrieval stable; one OperationalError recorded.","Process exited 0 because the fixture reports partial status in JSON; ambiguous retry outcome proves embedded local-Qdrant concurrency is flaky.",fixture_sha["mem0_fixture.py"],freeze_sha["mem0"])
smoke("MEM0-FINGERPRINTED-REPEAT-3","MEM0","fingerprinted Mem0 embedded-Qdrant concurrency fixture","same-version bounded repeat","PASS",77,"8/8 API returns; 8 persisted; stable post-concurrency retrieval; governance, deletion, export and egress checks passed.","Current fixture version; aggregate disposition remains FLAKY/PARTIAL.",fixture_sha["mem0_fixture.py"],freeze_sha["mem0"])
smoke("LLAMAINDEX-CORE","LLAMAINDEX","SimpleVectorStore persistence","deterministic fixture","PASS",32,"Stable source lineage; deterministic ranking; JSON persist/reload; export.","Two-node synthetic corpus only.")
smoke("LLAMAINDEX-QDRANT","LLAMAINDEX;QDRANT","LlamaIndex QdrantVectorStore + embedded qdrant-client","storage combination fixture","PASS",48,"Promotion/revocation filters; deletion; five repeated retrievals; export/reload; socket guard saw zero external egress attempts.","Local payload-index warning; no server/auth/replication/backup.")
smoke("UNSTRUCTURED-MD","UNSTRUCTURED","Markdown partition and JSON staging","deterministic fixture","PASS",33,"Four deterministic IDs; parent lineage; fixed metadata; JSON round-trip.","Structural Markdown only.")
smoke("UNSTRUCTURED-TEXT","UNSTRUCTURED","text partition stricter fixture","deterministic/concurrency fixture","PASS",50,"Six concurrent deterministic partitions; source lineage; export/reload; zero egress attempts.","Pinned 3.8.0 spaCy model was staged by a separate network command; broader formats untested.")
smoke("GRAPHITI-INSTALL","GRAPHITI","graphiti-core source package","install attempted","PASS",30,"Package installed in isolated Python 3.11 venv.","No graph database or hosted/local LLM provider.")
smoke("GRAPHITI-IMPORT","GRAPHITI","module import and telemetry opt-out","import smoke","PASS",47,"Import passed and is_telemetry_enabled() returned false.","Not a graph ingest/search fixture.")
smoke("GRAPHITI-KUZU-CRUD-HISTORICAL","GRAPHITI","EntityNode CRUD on local Kuzu adapter","bounded graph-storage fixture","PASS_BOUNDED_CRUD_SUPERSEDED",71,"Entity save/get; lineage metadata; governance update; group isolation; export/reload; hard delete; zero egress attempts.","Superseded by the fingerprinted repeat at sequence 78; Kuzu is deprecated.")
smoke("GRAPHITI-KUZU-FINGERPRINTED","GRAPHITI","EntityNode CRUD on local Kuzu adapter","bounded graph-storage fixture","PASS_BOUNDED_CRUD",78,"Entity save/get; lineage metadata; governance update; group isolation; export/reload; hard delete; zero egress attempts.","Kuzu is deprecated; no episode extraction, temporal-edge search, supported graph server, LLM, concurrency, backup or HA.",fixture_sha["graphiti_kuzu_fixture.py"],freeze_sha["graphiti"])
for test_id,candidate_id,component,why in [
    ("LETTA-NOT-RUN","LETTA","legacy + active successor runtime","Assigned repo deprecated; successor needs Node/provider/runtime scope."),
    ("PGVECTOR-NOT-RUN","PGVECTOR","PostgreSQL extension","Architecture-only addition; no local PostgreSQL service provisioned."),
    ("QDRANT-SERVER-NOT-RUN","QDRANT","Qdrant server","Embedded adapter tested instead; server operational proof deferred."),
    ("MINIO-NOT-RUN","MINIO","MinIO server","Architecture-only addition and code adoption blocked by AGPL/unmaintained status."),
]:
    smoke_rows.append({"test_id":test_id,"candidate_id":candidate_id,"component":component,"proof_level":"source inspected","status":"NOT_RUN","command":"","exit_code":"","duration_seconds":"","stdout_path":"","stdout_sha256":"","stderr_path":"","stderr_sha256":"","checks_passed":"Source/README/license inspected.","limitations":why,"fixture_sha256":"","environment_freeze_sha256":""})
write_csv("deployment-smoke-results.csv", list(smoke_rows[0].keys()), smoke_rows)

resource_rows = [
    {"candidate_id":"LETTA","profile_scope":"source checkout only","status":"NOT_RUN_RUNTIME","elapsed_seconds":"","max_rss_bytes":"","env_disk_kb":"","repo_disk_kb":33932+84352,"state_disk_kb":"","idle_cpu_percent":"UNKNOWN","idle_ram_bytes":"UNKNOWN","ports":"none started","measurement_evidence":evidence(45),"limitations":"Legacy and successor checkout combined; no runtime."},
    {"candidate_id":"MEM0","profile_scope":"timed core fixture","status":"PASS","elapsed_seconds":"0.67","max_rss_bytes":94732288,"env_disk_kb":197096,"repo_disk_kb":54680,"state_disk_kb":"shared lab storage 1252 KB at measurement","idle_cpu_percent":"N/A exited","idle_ram_bytes":"N/A exited","ports":"none","measurement_evidence":evidence(34)+"; "+evidence(45),"limitations":"Synthetic tiny corpus; max RSS includes Python and embedded adapters."},
    {"candidate_id":"GRAPHITI","profile_scope":"timed bounded Kuzu CRUD fixture","status":"PASS_BOUNDED_CRUD_ONLY","elapsed_seconds":"0.70","max_rss_bytes":181469184,"env_disk_kb":130976,"repo_disk_kb":29504,"state_disk_kb":1072,"idle_cpu_percent":"N/A exited","idle_ram_bytes":"N/A exited","ports":"none","measurement_evidence":evidence(72)+"; "+evidence(45),"limitations":"Kuzu adapter is deprecated; no supported graph server, LLM, concurrency, backup, HA or idle-service profile."},
    {"candidate_id":"LLAMAINDEX","profile_scope":"timed core persistence fixture","status":"PASS","elapsed_seconds":"0.87","max_rss_bytes":145227776,"env_disk_kb":235788,"repo_disk_kb":831144,"state_disk_kb":"shared lab storage 1252 KB at measurement","idle_cpu_percent":"N/A exited","idle_ram_bytes":"N/A exited","ports":"none","measurement_evidence":evidence(35)+"; "+evidence(45),"limitations":"Large monorepo checkout; tiny corpus."},
    {"candidate_id":"UNSTRUCTURED","profile_scope":"timed Markdown fixture","status":"PASS","elapsed_seconds":"1.15","max_rss_bytes":194281472,"env_disk_kb":392472,"repo_disk_kb":291356,"state_disk_kb":"shared lab storage 1252 KB at measurement","idle_cpu_percent":"N/A exited","idle_ram_bytes":"N/A exited","ports":"none","measurement_evidence":evidence(36)+"; "+evidence(45),"limitations":"Environment later grew after pinned spaCy model staging; no OCR/table model profile."},
    {"candidate_id":"PGVECTOR","profile_scope":"source checkout only","status":"NOT_RUN_RUNTIME","elapsed_seconds":"","max_rss_bytes":"","env_disk_kb":"","repo_disk_kb":1368,"state_disk_kb":"","idle_cpu_percent":"UNKNOWN","idle_ram_bytes":"UNKNOWN","ports":"none started","measurement_evidence":evidence(45),"limitations":"No PostgreSQL service or extension."},
    {"candidate_id":"QDRANT","profile_scope":"embedded client inside Mem0/LlamaIndex venvs","status":"PASS_ADAPTER_ONLY","elapsed_seconds":"included above","max_rss_bytes":"included above","env_disk_kb":"shared","repo_disk_kb":38328,"state_disk_kb":"shared lab storage 1252 KB at measurement","idle_cpu_percent":"N/A embedded","idle_ram_bytes":"N/A embedded","ports":"none","measurement_evidence":evidence(48)+"; "+evidence(45),"limitations":"No standalone server profile."},
    {"candidate_id":"MINIO","profile_scope":"source checkout only","status":"NOT_RUN_RUNTIME","elapsed_seconds":"","max_rss_bytes":"","env_disk_kb":"","repo_disk_kb":64060,"state_disk_kb":"","idle_cpu_percent":"UNKNOWN","idle_ram_bytes":"UNKNOWN","ports":"none started","measurement_evidence":evidence(45),"limitations":"No server runtime due architecture-only/license gate."},
]
write_csv("resource-profile.csv", list(resource_rows[0].keys()), resource_rows)

contract_rows = [
    {"candidate_id":"LETTA","capability":"working state/memory classes","native_support":"yes conceptually","fixture_proof":"none","fit_status":"REJECT_FIT","wrapper_required":"N/A for direct adoption; study concepts only","risk":"Legacy server deprecated; successor is a self-modifying agent harness overlapping Helixar/Hermes authority and telemetry is enabled by default.","evidence":"R01-O009; repos/letta/AGENTS.md:3-18; repos/letta-code/src/index.ts:980-983"},
    {"candidate_id":"MEM0","capability":"scoped CRUD/search/history/delete","native_support":"yes","fixture_proof":"FLAKY/PARTIAL: current fingerprinted fixture passed 2/3; one run had 7/8 API returns with 8 persisted rows","fit_status":"ADAPT_WITH_SERIALIZED_OR_SERVER_WRITER_POC","wrapper_required":"proposal/approval/revocation state machine; immutable audit; CAS/idempotency; deterministic score tolerance/tie-break","risk":"Embedded local-Qdrant concurrency is intermittent; persistence despite an API error complicates retry/idempotency; scores are not bit-exact; telemetry defaults on.","evidence":evidence(75)+"; "+evidence(76)+"; "+evidence(77)},
    {"candidate_id":"GRAPHITI","capability":"bitemporal facts, episodes and provenance","native_support":"yes by source/docs","fixture_proof":"bounded Kuzu EntityNode CRUD PASS","fit_status":"POC_MORE","wrapper_required":"hard privacy deletion; governance approvals; canonical source/claim contracts; supported graph backend","risk":"Tested Kuzu backend is deprecated; LLM extraction, temporal-edge search, supported database operations and concurrency remain unproven; telemetry enabled.","evidence":evidence(78)+"; repos/graphiti/README.md:42-49,65-82,120-136,160-170"},
    {"candidate_id":"LLAMAINDEX","capability":"nodes, deterministic retrieval, persistence and adapters","native_support":"yes","fixture_proof":"PASS","fit_status":"ADAPT_BOUNDED_RETRIEVAL","wrapper_required":"governance state/audit; stable export schema; orchestration kept outside","risk":"Dependency/component churn and default hosted model resolution if local embedder omitted.","evidence":evidence(32)+"; "+evidence(48)},
    {"candidate_id":"UNSTRUCTURED","capability":"partition, metadata lineage and export","native_support":"yes","fixture_proof":"PASS on text/Markdown","fit_status":"ADAPT_AFTER_GOLDEN_CORPUS","wrapper_required":"source digest envelope; prompt-injection quarantine; memory governance outside parser","risk":"Heavy dependencies; format variance; optional runtime model download.","evidence":evidence(33)+"; "+evidence(50)},
    {"candidate_id":"PGVECTOR","capability":"ACID metadata + vector search","native_support":"yes by source","fixture_proof":"not run","fit_status":"ARCHITECTURE_CANDIDATE","wrapper_required":"tenant schema, audit append-only rules, migration/backup policy","risk":"Operational PostgreSQL ownership and index tuning unproven.","evidence":"repos/pgvector/README.md:1-34,53-128"},
    {"candidate_id":"QDRANT","capability":"payload-filtered vector retrieval","native_support":"yes","fixture_proof":"embedded adapter PASS","fit_status":"ADAPT_RETRIEVAL_INDEX","wrapper_required":"canonical truth remains PostgreSQL/object/audit layer; explicit tenant/filter contracts","risk":"Local mode lacks effective payload indexes; server quickstart insecure by default; HA/auth unproven.","evidence":evidence(48)+"; repos/qdrant/README.md:44-62"},
    {"candidate_id":"MINIO","capability":"S3-compatible object storage","native_support":"yes by source","fixture_proof":"not run","fit_status":"REJECT_CODE_ADOPTION","wrapper_required":"content-addressed keys, retention, legal/licensing boundary","risk":"AGPL-3.0; repository unmaintained/source-only; commercial successor not source-equivalent.","evidence":"repos/minio/README.md:1-7,26-47,166-170"},
]
write_csv("contract-fit.csv", list(contract_rows[0].keys()), contract_rows)

cleanup_rows = [
    {"item_id":"CLN-01","candidate_id":"ALL","path_or_resource":str(LAB / "repos"),"resource_type":"shallow source checkouts","created_by_lane":"true","cleanup_action":"rm -rf after evidence retention is no longer required","status":"RETAINED_FOR_REPRODUCIBILITY","verification":"all candidate repos clean at exact commits","evidence":evidence(45)},
    {"item_id":"CLN-02","candidate_id":"MEM0;GRAPHITI;LLAMAINDEX;UNSTRUCTURED","path_or_resource":str(LAB / "envs"),"resource_type":"isolated virtual environments","created_by_lane":"true","cleanup_action":"rm -rf after handoff","status":"READY_FOR_CLEANUP","verification":"isolated outside implementation repositories","evidence":evidence(45)},
    {"item_id":"CLN-03","candidate_id":"MEM0;GRAPHITI;LLAMAINDEX;QDRANT;UNSTRUCTURED","path_or_resource":str(LAB / "storage"),"resource_type":"synthetic local state","created_by_lane":"true","cleanup_action":"rm -rf after handoff; no customer/business data","status":"RETAINED_AS_FIXTURE_EVIDENCE","verification":"all paths under disposable lab root","evidence":evidence(32)+"; "+evidence(48)+"; "+evidence(50)+"; "+evidence(76)+"; "+evidence(78)},
    {"item_id":"CLN-04","candidate_id":"ALL","path_or_resource":str(LAB / "exports"),"resource_type":"synthetic fixture exports","created_by_lane":"true","cleanup_action":"retain with lab or remove with lab root","status":"RETAINED_AS_EVIDENCE","verification":"synthetic .invalid/fixture inputs only","evidence":evidence(32)+"; "+evidence(48)+"; "+evidence(50)+"; "+evidence(76)+"; "+evidence(78)},
    {"item_id":"CLN-05","candidate_id":"ALL","path_or_resource":"candidate services/processes","resource_type":"process/port","created_by_lane":"false (no persistent candidate service started)","cleanup_action":"none","status":"CLEAN","verification":"no candidate server was started; detached validator checks candidate ports and processes","evidence":"process-log.jsonl; artifacts/final-validation.json"},
    {"item_id":"CLN-06","candidate_id":"ALL","path_or_resource":"implementation repositories/business systems","resource_type":"external write surface","created_by_lane":"false","cleanup_action":"none","status":"UNCHANGED_BY_O02","verification":"no implementation repo or business connector command exists in process log","evidence":"process-log.jsonl; network-fetch-log.jsonl"},
]
write_csv("cleanup-manifest.csv", list(cleanup_rows[0].keys()), cleanup_rows)

status_counts = Counter("PASS" if row["status"].startswith("PASS") else row["status"] for row in smoke_rows)
repo_lines = []
for key in ["Letta","Letta current (letta-code)","Mem0","Graphiti","LlamaIndex","Unstructured","PostgreSQL+pgvector","Qdrant","MinIO"]:
    row=manifest[key]
    repo_lines.append(f"- `{row['path']}` — `{row['commit']}`; tree `{row['tree_hash']}`; {row['repository_url']}")

drift_lines = "\n".join(f"- `{row['path']}` changed from frozen `{row['expected_sha256']}` to `{row['current_sha256']}` before O02 deliverable writes; treated as concurrent shared-vault drift, not silently accepted." for row in mandatory_drift)
report = f"""---
title: O02 Brain, Memory, Retrieval and Storage OSS Lab Report
date: 2026-07-14
status: validated-bounded-pass-with-disclosed-gaps
wave: A
lane: O02
---

# O02 Brain, Memory, Retrieval and Storage OSS Lab Report

Links: [[00 Helixar World-Class Benchmark Program - Control Center]] · [[02 Current Architecture Benchmark]] · [[04 Cross-Packet Implementation Readiness Audit - 2026-07-14]] · [[05 Hermes Parallel Architecture and Build Roadmap]] · [[R01 Sol-Fleet Research and Architecture Packet]] · [[Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab]]

## Executive verdict

**Use LlamaIndex core + a Qdrant retrieval adapter as the first bounded retrieval path, but keep canonical truth, approvals, revocation, lineage validation and audit outside both tools.** The embedded combination passed deterministic ranking, metadata governance filters, deletion, export/reload and an explicit socket egress guard. This is adapter proof—not Qdrant server production proof.

**Mem0 is `ADAPT`, not autonomous truth, and embedded local-Qdrant concurrency is `FLAKY/PARTIAL`.** The current fingerprinted fixture passed two of three identical-version repeats. The partial run returned 7/8 successful API results while all eight rows persisted and logged `OperationalError: cannot commit - no transaction is active`; post-concurrency reads remained stable. This ambiguous retry outcome requires a serialized or server-backed writer POC, idempotency/CAS, stable-ID tie-break, bounded score tolerance and independent immutable governance audit.

**Unstructured is `ADAPT` for ingestion after a real golden corpus.** Text/Markdown lineage, deterministic IDs, concurrent partitioning and JSON export/reload passed. OCR, tables, slides, spreadsheets and adversarial document handling remain unknown. Its isolated environment was the heaviest tested environment.

**Graphiti is `POC_MORE`.** A fingerprinted bounded Kuzu fixture passed entity CRUD, lineage metadata, governance update, group exclusion, JSON export/reload and hard deletion with zero egress attempts. Kuzu is deprecated; episode extraction, temporal-edge search, a supported graph backend, structured-output LLM, concurrency, backup and production operations remain unproven.

**Letta is concepts-only for now.** The assigned `letta` repository now declares itself legacy; current work moved to `letta-code`/Agent SDK. Both exact source commits were inspected, but no current local runtime was exercised.

**PostgreSQL+pgvector is the leading canonical metadata/governance-store architecture candidate, but was not run.** Qdrant server was not run. **Reject direct MinIO community-source adoption** for this proprietary system unless legal explicitly accepts AGPL and the unmaintained/source-only posture; evaluate a commercial partner or another S3-compatible implementation instead.

## Recommended bounded architecture

1. PostgreSQL + pgvector candidate for canonical tenant-scoped records, lifecycle state, idempotency, approvals, revocations and audit linkage.
2. Content-addressed object storage interface for immutable source/export blobs; implementation choice remains open because MinIO community source is blocked.
3. LlamaIndex core as document/node/retrieval adapter.
4. Qdrant as a replaceable derived retrieval index, never source of truth.
5. Unstructured as a quarantined ingestion adapter after corpus-specific acceptance.
6. Graphiti only after evidence shows flat retrieval cannot meet temporal/provenance needs.
7. Mem0 only behind a serialized writer and deterministic projection wrapper; never automatic global promotion.

## Proof ladder

| Candidate | Source | Install | Service/CLI | Deterministic fixture | Integration fit | Production suitability |
|---|---:|---:|---:|---:|---:|---:|
| Letta | PASS (legacy + successor) | NOT RUN | NOT RUN | NOT RUN | Not proven | Unknown |
| Mem0 | PASS | PASS | N/A library | FLAKY/PARTIAL (2/3 current repeats passed) | Partial behind wrapper | Unknown |
| Graphiti | PASS | PASS | N/A library | PASS bounded CRUD only | Partial | Unknown |
| LlamaIndex | PASS | PASS | N/A library | PASS | Proven for bounded retrieval | Unknown |
| Unstructured | PASS | PASS | N/A library | PASS | Proven for text/Markdown ingestion | Unknown |
| PostgreSQL+pgvector | PASS | NOT RUN | NOT RUN | NOT RUN | Architecture only | Unknown |
| Qdrant | PASS | Embedded client only | Server NOT RUN | PASS embedded | Partial | Unknown |
| MinIO | PASS | NOT RUN | NOT RUN | NOT RUN | Blocked | Unknown |

## Real fixture outcomes

- Mem0 core fixture: `{evidence(31)}`.
- Mem0 fingerprinted repeated probe: `{evidence(75)}` PASS; `{evidence(76)}` `FLAKY_PARTIAL` with 7/8 successful API returns but eight persisted rows; `{evidence(77)}` PASS. Fixture SHA-256 `{fixture_sha['mem0_fixture.py']}` and environment-freeze SHA-256 `{freeze_sha['mem0']}` were constant across repeats.
- Mem0 earlier-variant falsification remains visible: `{evidence(38)}` captured an embedded-Qdrant SQLite concurrency failure and `{evidence(54)}` captured a bit-exact score/order assertion failure. Historical fixture hashes were not captured, so these are not mislabeled as same-version repeats.
- LlamaIndex core fixture: `{evidence(32)}`.
- LlamaIndex + embedded Qdrant storage fixture: `{evidence(48)}`. Five repeated retrievals, metadata promotion/revocation, deletion, export/reload and zero denied external egress attempts passed.
- Unstructured Markdown fixture: `{evidence(33)}`.
- Unstructured text/concurrency fixture: `{evidence(50)}`.
- Graphiti import/telemetry opt-out: `{evidence(47)}`.
- Graphiti fingerprinted bounded Kuzu CRUD: `{evidence(78)}`; fixture SHA-256 `{fixture_sha['graphiti_kuzu_fixture.py']}` and environment-freeze SHA-256 `{freeze_sha['graphiti']}`.

The exact row-level evidence is in [[candidate-inventory]], [[deployment-smoke-results]], [[resource-profile]], [[license-and-security]], [[contract-fit]] and [[cleanup-manifest]].

## Source, license and security findings

- Mem0 and Graphiti telemetry default to enabled and target PostHog; their environment opt-outs must be set before import/initialization.
- Unstructured telemetry is opt-in/off by default at this commit; the tested environment still set all documented opt-outs.
- Qdrant's own quickstart warns that the default container is insecure and exposed to all interfaces. No server was started in this lane.
- MinIO declares the community repository unmaintained and source-only, under AGPL-3.0.
- Exact repository/license hashes are retained in `candidate-source-manifest.json` and `license-and-security.csv`.
- Sanitized `pip check` passed in all four isolated candidate environments after inherited Python environment variables were removed: `{evidence(73)}`. No package removal was needed.
- `pip-audit` findings were confined to old `pip`/`setuptools` installer tooling; no audited candidate runtime package was named.

## Resource observations

| Candidate | Timed scope | Elapsed | Max RSS | Environment disk |
|---|---|---:|---:|---:|
| Mem0 | lifecycle fixture | 0.67 s | 94,732,288 B | 197,096 KB |
| LlamaIndex | core fixture | 0.87 s | 145,227,776 B | 235,788 KB |
| Unstructured | Markdown fixture | 1.15 s | 194,281,472 B | 392,472 KB after pinned-model staging |
| Graphiti | bounded Kuzu CRUD | 0.70 s | 181,469,184 B | 130,976 KB |

No candidate service remained idle, so idle CPU/RAM are `N/A`; exited-process peak RSS is the honest measurement. Full details and limitations are in `resource-profile.csv`.

## Network and external effects

- Recorded public-network command envelopes before receipt/final gate: **{len(network)}**.
- Lower-level HTTP request count inside Git/pip: **unknown**; no packet capture was used.
- Loopback candidate-service HTTP requests: **0**.
- External business-system writes: **0**.
- Credentials/customer data/live connectors used: **0**.
- Persistent candidate services started: **0**.
- Synthetic state and exports remained under `{LAB}`.

## Source immutability and parallel-work disclosure

All **{len(source_csv_results)}** frozen R01-R10 inventory/evidence CSVs remain byte-for-byte unchanged: `{all(row['unchanged'] for row in source_csv_results)}`.

The original broad manifest also froze shared control/current-state/daily-log notes. Three changed during the parallel program before O02 wrote its deliverables:

{drift_lines}

O02 did not overwrite or roll back those sibling additions. Therefore the strict original 30-file manifest gate is **BLOCKED_CONCURRENT_DRIFT**, while the immutable inventory/evidence source-CSV gate is **PASS**. The detached post-receipt validator rechecks the frozen CSV corpus directly.

## Exact repositories read

{chr(10).join(repo_lines)}

Exact architecture/evidence file reads are enumerated in `{LAB / 'source-hash-manifest.json'}` (30 absolute paths). Exact candidate metadata/license reads are enumerated in `{LAB / 'candidate-source-manifest.json'}`.

## Files written

- `{REPORT}`
- `{DATA / 'candidate-inventory.csv'}`
- `{DATA / 'license-and-security.csv'}`
- `{DATA / 'deployment-smoke-results.csv'}`
- `{DATA / 'resource-profile.csv'}`
- `{DATA / 'contract-fit.csv'}`
- `{DATA / 'cleanup-manifest.csv'}`
- `04_Logs/Runs/Run Receipt - 2026-07-14 - O02 Brain Memory OSS Lab.md`

Disposable lab scripts, fixtures, state, exports and logs are retained under `{LAB}` and are listed by `cleanup-manifest.csv`.

## Human decisions required

1. Approve or reject PostgreSQL+pgvector as canonical governance/metadata storage after a dedicated server/backup/tenant-isolation lab.
2. Approve Qdrant server evaluation or keep embedded/derived retrieval only.
3. Decide whether Mem0 remains a contract/fixture source or receives a serialized-writer POC.
4. Decide whether Graphiti's temporal graph benefit justifies database + LLM operational cost.
5. Select an S3-compatible object store; direct MinIO community-source adoption is blocked by AGPL/unmaintained status.
6. Decide whether current Letta Agent SDK/App Server merits a separate Node 22.19+ offline runtime lab.

## Deliverable acceptance

| Deliverable | Status |
|---|---|
| Report | PASS |
| candidate-inventory.csv | WRITTEN; 8/8 candidates |
| license-and-security.csv | WRITTEN; exact commits/licenses |
| deployment-smoke-results.csv | WRITTEN; PASS and FAIL evidence paths/hashes |
| resource-profile.csv | WRITTEN; unknowns not fabricated |
| contract-fit.csv | WRITTEN |
| cleanup-manifest.csv | WRITTEN |
| Dated run receipt | PASS |
| No implementation/business mutation | PASS |
| Loopback exposure | PASS at detached gate; no candidate service was started |
| Candidate environment dependency consistency | PASS: sanitized `pip check` passed in all four isolated venvs (sequence 73) |
| Memory/retrieval smoke minimum | PASS_BOUNDED: LlamaIndex and Graphiti bounded fixtures passed; Qdrant passed through the LlamaIndex combination; Mem0 remains FLAKY/PARTIAL |
| Original broad source manifest | BLOCKED_CONCURRENT_DRIFT |
| Frozen R01-R10 inventory/evidence CSVs | PASS |

Do not promote this lab to production approval. Wave A established bounded local deployability evidence and explicit blockers only.
"""
REPORT.write_text(report, encoding="utf-8")
print(json.dumps({
    "report": str(REPORT),
    "data_dir": str(DATA),
    "candidate_count": len(candidates),
    "smoke_rows": len(smoke_rows),
    "network_command_envelopes": len(network),
    "source_csv_unchanged": all(row["unchanged"] for row in source_csv_results),
    "mandatory_context_drift_count": len(mandatory_drift),
}, indent=2, sort_keys=True))
