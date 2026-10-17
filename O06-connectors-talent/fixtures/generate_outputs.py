#!/usr/bin/env python3
"""Generate O06 evidence tables, architecture report, and run receipt."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
DYSTOPIA = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
OUT = DYSTOPIA / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O06-connectors-talent"
REPORT = DYSTOPIA / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O06 Connector, GTM and Talent OSS Lab Report.md"
RECEIPT = DYSTOPIA / "04_Logs/Runs/2026-07-14 - O06 Connector GTM and Talent OSS Lab Run Receipt.md"
OUT.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)

metadata = {row["candidate"]: row for row in json.loads((LAB / "artifacts/candidate-metadata.json").read_text())}
archive_hashes = {
    "Activepieces": "25e7182c8b14f2647968c4adda0b5aaf663c66ddc7ad0514268ce8774a7657b2",
    "Nango": "4aed335e892fc518110e658519804c44c9a0a1348a6bc536bb00fb8940f66dc1",
    "Twenty": "cfdfaf801b7635bdd5a315aded23770e70e892974104274162c42b9f6dee7222",
    "Apache Unomi": "6e7b0f265e7d7e8b0baba8194cd4b89b944db727b59d500a595b0ae49b418b4a",
    "OpenFGA": "67566948bac9d2c5e52c9a804916ac2e585967cb3327bb61ffa4b11c269f63b1",
    "Klaro": "6ffa5457ea551f79b2a38547723e0344b8b3f2b23a2a50f2de616adf2bba5f7b",
    "dedupe": "fddb3ac93ee5a39d30110e72f0cc1e1cdbe1f583ac2748090573276194f1fb8c",
    "OpenCATS": "bbe7e7f4667fdd9755d1374efb6cb97b3ea426e15db37da275ff7ac3f0fb9c8a",
    "Frappe HR": "792fb9eeb805ae7a9cf49c128253b7a9c7bb08b1073b10677017661b74ec0f0e",
}

inventory_rows = [
    dict(candidate="Activepieces", lane="R07 Mars-GTM", role="connector/workflow framework", relevance="Large community piece catalog and auth abstractions", prior_inventory_refs="R01;R07;R10", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", classification="POC_MORE", decision_basis="Promising core connector fabric; mixed MIT/enterprise path boundary and full-stack operations were not exercised"),
    dict(candidate="Nango", lane="R07 Mars-GTM;R10 Mercury-Talent", role="connector/auth/sync framework", relevance="Typed connector manifests, auth lifecycle, sync/action runtime", prior_inventory_refs="R01;R07;R10", source_inspected="true", install_attempted="true (CLI only)", service_or_cli_started="true (CLI)", deterministic_fixture_passed="true (compile/manifest)", integration_fit_proven="false", production_suitability="UNKNOWN", classification="PARTNER", decision_basis="Best connector developer experience in this lab, but ELv2 plus all-rights-reserved areas block unreviewed source adoption"),
    dict(candidate="Twenty", lane="R07 Mars-GTM", role="CRM/customer workspace reference", relevance="Workspace-scoped CRM objects, people, pipelines and export/delete surfaces", prior_inventory_refs="R07", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", classification="REJECT_LICENSE", decision_basis="AGPLv3/commercial split is incompatible with unreviewed embedding; consider commercial partner path only"),
    dict(candidate="Apache Unomi", lane="R07 Mars-GTM", role="customer data/profile reference", relevance="Profiles, events, consent and personalization", prior_inventory_refs="R07", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", classification="REJECT_OPERATIONS", decision_basis="Apache-2.0 is clear, but Java/Karaf plus Elasticsearch is disproportionate for the bounded connector/consent role"),
    dict(candidate="OpenFGA", lane="R07 Mars-GTM;R10 Mercury-Talent", role="fine-grained authorization", relevance="Tenant/resource authorization relation engine", prior_inventory_refs="R01;R02;R07;R10", source_inspected="true", install_attempted="true", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", classification="POC_MORE", decision_basis="Strong Apache-2.0 authorization fit; source build lacked Go and release extraction was approval-blocked, so no authorization PASS"),
    dict(candidate="Klaro", lane="R07 Mars-GTM", role="consent manager", relevance="Default-deny consent, service callbacks, cookie suppression and consent reset", prior_inventory_refs="R07", source_inspected="true", install_attempted="false (source bundled)", service_or_cli_started="false", deterministic_fixture_passed="true (component)", integration_fit_proven="true (isolated component contract)", production_suitability="UNKNOWN", classification="ADAPT", decision_basis="BSD-3 component passed synthetic default-deny, withdrawal, suppression and reset fixture"),
    dict(candidate="dedupe", lane="R07 Mars-GTM", role="entity resolution library", relevance="Deterministic customer/person record clustering", prior_inventory_refs="R07;R10", source_inspected="true", install_attempted="true", service_or_cli_started="false (library fixture)", deterministic_fixture_passed="true (library)", integration_fit_proven="true (tenant-partitioned adapter contract)", production_suitability="UNKNOWN", classification="ADAPT", decision_basis="MIT library clustered synthetic identities; tenant isolation must be imposed before candidate generation"),
    dict(candidate="OpenCATS", lane="R10 Mercury-Talent", role="ATS reference", relevance="Candidate pipeline, human status changes, history and selected export", prior_inventory_refs="R10", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="true (source/UI/schema)", integration_fit_proven="false", production_suitability="UNKNOWN", classification="REJECT_LICENSE", decision_basis="Useful ATS contract reference; mixed MPL-2.0/CATS Public License and unavailable PHP 8.4.1 block code adoption/deployment"),
    dict(candidate="Frappe HR", lane="R10 Mercury-Talent", role="HR/ATS reference", relevance="Job applicant/offer links, onboarding states, role-gated submit/export/delete", prior_inventory_refs="R10", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="true (schema/controller)", integration_fit_proven="false", production_suitability="UNKNOWN", classification="REJECT_OPERATIONS", decision_basis="GPL-3.0 source is inspectable, but Frappe+ERPNext v17 stack was not feasible in this bounded lane"),
]
for row in inventory_rows:
    m = metadata[row["candidate"]]
    row.update(primary_repository=m["repository"], selected_commit=m["commit"], source_archive_sha256=archive_hashes[row["candidate"]], commit_date=m["commit_date"], exact_tag=m["exact_tag"] or "none")

license_rows = [
    dict(candidate="Activepieces", license_class="MIT outside named enterprise paths; Activepieces Enterprise License inside packages/ee and named server EE path", license_files="LICENSE;packages/ee/LICENSE", code_adoption_boundary="Do not copy or depend on enterprise-marked paths without commercial approval; isolate and verify core-only dependency graph", security_policy="SECURITY.md present", auth_secret_handling="Source auth abstractions found; no token runtime test", telemetry_egress="Sentry/telemetry code present and configuration-dependent; not runtime-tested", known_security_ops_notes="Full server not installed; secret encryption, tenant keying and SSRF controls remain unknown", license_decision="POC_MORE core-only after legal/path audit"),
    dict(candidate="Nango", license_class="Elastic License 2.0 plus LICENSE_SHORT all-rights-reserved notice", license_files="LICENSE;LICENSE_SHORT", code_adoption_boundary="No unreviewed server/source embedding; CLI fixture use only; commercial partnership path preferred", security_policy="SECURITY.md present", auth_secret_handling="Keystore/encryption and connection-ID scoping inspected in source; no server/real token test", telemetry_egress="CLI telemetry is enabled unless --no-telemetry or NANGO_CLI_TELEMETRY=false; two lab CLI commands may have POSTed anonymous events", known_security_ops_notes="CLI install emitted deprecated inflight/glob warnings; server data plane not started", license_decision="PARTNER; legal review before any code adoption"),
    dict(candidate="Twenty", license_class="AGPLv3 for most project plus commercial enterprise-marked files", license_files="LICENSE", code_adoption_boundary="Reject embedding/forking in this wave; commercial partner evaluation is a separate human decision", security_policy=".github/SECURITY.md present", auth_secret_handling="Workspace scoping and person lifecycle source inspected; no runtime isolation test", telemetry_egress="Self-hosting telemetry/billing app and analytics/Sentry surfaces present; defaults not runtime-verified", known_security_ops_notes="Large multi-service CRM and mixed-license file-level boundary", license_decision="REJECT_LICENSE for source adoption"),
    dict(candidate="Apache Unomi", license_class="Apache-2.0", license_files="LICENSE", code_adoption_boundary="Permissive; preserve notices", security_policy="SECURITY.md present", auth_secret_handling="Profile/consent/delete APIs inspected; no tenant/auth runtime test", telemetry_egress="No lab runtime; Java/Elasticsearch dependency egress not observed", known_security_ops_notes="Karaf/Elasticsearch operational and historical attack-surface review required", license_decision="License acceptable; operations rejected for current role"),
    dict(candidate="OpenFGA", license_class="Apache-2.0", license_files="LICENSE", code_adoption_boundary="Permissive; preserve notices", security_policy=".github/SECURITY-INSIGHTS.yml present; no conventional SECURITY.md in clone", auth_secret_handling="Authorization model and bind/telemetry flags inspected; auth service did not start", telemetry_egress="OpenTelemetry exporters are configurable/experimental; no runtime egress", known_security_ops_notes="No Go/Java/Docker prerequisites; fetched v1.18.1 release artifact was not extracted or executed", license_decision="POC_MORE in an approved toolchain/container"),
    dict(candidate="Klaro", license_class="BSD-3-Clause", license_files="LICENSE", code_adoption_boundary="Permissive; retain notice", security_policy="No SECURITY file found", auth_secret_handling="Not a token store", telemetry_egress="Fixture made zero external requests; service scripts are application-configured", known_security_ops_notes="Component is client-side consent state, not authoritative suppression/audit storage", license_decision="ADAPT behind server-side suppression ledger"),
    dict(candidate="dedupe", license_class="MIT", license_files="LICENSE", code_adoption_boundary="Permissive; retain notice", security_policy="No SECURITY file found", auth_secret_handling="No credentials/token surface", telemetry_egress="Fixture sent zero messages and made no network requests", known_security_ops_notes="Tenant boundary is not native; pre-partition candidate sets and audit merges", license_decision="ADAPT as bounded entity-resolution library"),
    dict(candidate="OpenCATS", license_class="MPL-2.0 plus nonstandard CATS Public License 1.1a for original code", license_files="LICENSE.md", code_adoption_boundary="No code copy/adoption until file provenance and modified license receive legal approval", security_policy="No SECURITY file found", auth_secret_handling="Permission checks inspected; no authenticated PHP runtime", telemetry_egress="No telemetry match in source search; no runtime", known_security_ops_notes="Requires PHP ^8.4.1 and database; legacy/mixed provenance raises maintenance risk", license_decision="REJECT_LICENSE"),
    dict(candidate="Frappe HR", license_class="GPL-3.0", license_files="license.txt", code_adoption_boundary="Reciprocal distribution obligations; no code embedding decision in Wave A", security_policy="SECURITY.md links Frappe security process", auth_secret_handling="DocType role permissions inspected; Frappe auth runtime not started", telemetry_egress="No HRMS runtime; frontend lock contains analytics-capable dependencies but activation unknown", known_security_ops_notes="Requires Frappe and ERPNext >=17,<18 plus database/queues", license_decision="License known; REJECT_OPERATIONS for bounded lane"),
]
for row in license_rows:
    m = metadata[row["candidate"]]
    row["commit"] = m["commit"]
    row["license_evidence_sha256"] = ";".join(f"{item['path']}={item['sha256']}" for item in m["licenses"])

smoke_rows = [
    dict(candidate="Activepieces", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", status="NOT_RUN", fixture_scope="None", command_evidence="logs/process-ledger.csv (clone and metadata only)", real_output="No deployment/fixture PASS", bind_port="none", synthetic_data="none", limitation="Full monorepo install exceeded selected bounded subset; Nango chosen as connector smoke"),
    dict(candidate="Nango", source_inspected="true", install_attempted="true (nango@0.71.0 CLI)", service_or_cli_started="true (CLI)", deterministic_fixture_passed="true", integration_fit_proven="false", production_suitability="UNKNOWN", status="PASS_CLI_FIXTURE", fixture_scope="Compiled generated GitHub sample plus mock-api action; validated manifest; independent loopback connector contract harness", command_evidence="logs/commands/20260714T232040+0530-nango_compile_synthetic.log;logs/commands/20260714T232106+0530-nango_manifest_check.log;logs/commands/20260714T233014+0530-mock_connector_api_smoke.log", real_output="Typechecking/build/artifact generation PASS; mock-api action present; 0 credential values; loopback health/tenant/export/delete/suppression PASS", bind_port="127.0.0.1:53176 (independent harness; stopped)", synthetic_data="tenant-a.invalid;tenant-b.invalid;fake Synthetic token-* values", limitation="Nango server/keystore and action-to-mock execution not run; token isolation is not proven for Nango"),
    dict(candidate="Twenty", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", status="NOT_RUN_LICENSE_GATE", fixture_scope="Source/license/workspace lifecycle inspection", command_evidence="logs/process-ledger.csv", real_output="No deployment/fixture PASS", bind_port="none", synthetic_data="none", limitation="AGPL/commercial boundary and heavy multi-service stack"),
    dict(candidate="Apache Unomi", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", status="NOT_RUN_PREREQUISITE", fixture_scope="Source profile/consent/delete inspection", command_evidence="logs/commands/20260714T225908+0530-prerequisites.log", real_output="Java runtime unavailable", bind_port="none", synthetic_data="none", limitation="No Java; Elasticsearch/Karaf stack not started"),
    dict(candidate="OpenFGA", source_inspected="true", install_attempted="true", service_or_cli_started="false", deterministic_fixture_passed="false", integration_fit_proven="false", production_suitability="UNKNOWN", status="NOT_RUN_PREREQUISITE", fixture_scope="Source/config/license plus release metadata/binary fetch", command_evidence="logs/commands/20260714T225908+0530-prerequisites.log;logs/commands/20260714T230735+0530-openfga_release_metadata.log;logs/commands/20260714T230826+0530-openfga_binary_fetch.log", real_output="go not found; v1.18.1 Darwin arm64 artifact fetched; extraction command approval-blocked", bind_port="none", synthetic_data="none", limitation="Binary was not extracted/executed; no authorization model PASS"),
    dict(candidate="Klaro", source_inspected="true", install_attempted="false (source bundled)", service_or_cli_started="false", deterministic_fixture_passed="true", integration_fit_proven="true (component)", production_suitability="UNKNOWN", status="PASS_COMPONENT_FIXTURE", fixture_scope="Actual consent-manager.js bundled and executed with synthetic browser store/cookie jar", command_evidence="logs/commands/20260714T231944+0530-klaro_component_bundle.log;logs/commands/20260714T232010+0530-klaro_consent_fixture.log", real_output="default deny, required service, accept persistence, withdrawal suppression and reset deletion PASS", bind_port="none", synthetic_data="lab.invalid;synthetic cookies", limitation="No browser UI/server-side consent receipt or regulatory review"),
    dict(candidate="dedupe", source_inspected="true", install_attempted="true", service_or_cli_started="false (library)", deterministic_fixture_passed="true", integration_fit_proven="true (adapter)", production_suitability="UNKNOWN", status="PASS_LIBRARY_FIXTURE", fixture_scope="Installed editable source in isolated venv; ran dedupe.clustering.cluster on tenant-partitioned synthetic identities", command_evidence="logs/commands/20260714T231658+0530-dedupe_tenant_fixture.log;logs/commands/20260714T231739+0530-dedupe_resource_profile.log", real_output="clusters (1,2) and (4,5); zero cross-tenant candidate edges; export then delete PASS", bind_port="none", synthetic_data="acme.invalid;beta.invalid", limitation="Partition enforced by O06 adapter, not native authorization"),
    dict(candidate="OpenCATS", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="true", integration_fit_proven="false", production_suitability="UNKNOWN", status="PASS_SOURCE_FIXTURE", fixture_scope="Executed actual js/pipeline.js in Node VM; asserted PHP permission guard strings and SQL hiring statuses/history", command_evidence="logs/commands/20260714T231821+0530-opencats_source_smoke.log", real_output="selected-candidate export, change/remove permission gates, five human hiring states and history table PASS", bind_port="none", synthetic_data="candidate-101..103", limitation="PHP/database service not installed; source/UI/schema smoke is not deployment proof"),
    dict(candidate="Frappe HR", source_inspected="true", install_attempted="false", service_or_cli_started="false", deterministic_fixture_passed="true", integration_fit_proven="false", production_suitability="UNKNOWN", status="PASS_SOURCE_FIXTURE", fixture_scope="Parsed Employee Onboarding DocType, compiled controller syntax, asserted role/export/delete contract", command_evidence="logs/commands/20260714T231854+0530-frappe_hr_source_smoke.log", real_output="Pending/In Process/Completed; HR Manager submit/export; System Manager delete PASS", bind_port="none", synthetic_data="schema-only", limitation="Frappe/ERPNext runtime not installed; no ATS service proof"),
]

resource_rows = [
    dict(candidate="Activepieces", source_clone_kib="299876", candidate_env_kib="0", install_duration_s="NOT_RUN", start_or_fixture_duration_s="NOT_RUN", idle_cpu="UNKNOWN", idle_ram_bytes="UNKNOWN", max_rss_bytes="UNKNOWN", ports="none", storage_note="Source only"),
    dict(candidate="Nango", source_clone_kib="417404", candidate_env_kib="352052", install_duration_s="14.583 CLI + 8.632 init", start_or_fixture_duration_s="4.085 compile; 0.556 independent contract harness", idle_cpu="N/A no persistent service", idle_ram_bytes="N/A no persistent service", max_rss_bytes="27656192 independent harness only", ports="127.0.0.1:53176 ephemeral/stopped", storage_note="envs/nango-cli plus generated fixture/node_modules"),
    dict(candidate="Twenty", source_clone_kib="469116", candidate_env_kib="0", install_duration_s="NOT_RUN", start_or_fixture_duration_s="NOT_RUN", idle_cpu="UNKNOWN", idle_ram_bytes="UNKNOWN", max_rss_bytes="UNKNOWN", ports="none", storage_note="Source only"),
    dict(candidate="Apache Unomi", source_clone_kib="33660", candidate_env_kib="0", install_duration_s="NOT_RUN", start_or_fixture_duration_s="NOT_RUN", idle_cpu="UNKNOWN", idle_ram_bytes="UNKNOWN", max_rss_bytes="UNKNOWN", ports="none", storage_note="Source only"),
    dict(candidate="OpenFGA", source_clone_kib="9236", candidate_env_kib="19252", install_duration_s="2.936 binary fetch; no install", start_or_fixture_duration_s="NOT_RUN", idle_cpu="UNKNOWN", idle_ram_bytes="UNKNOWN", max_rss_bytes="UNKNOWN", ports="none", storage_note="v1.18.1 tarball+SBOM retained; not extracted"),
    dict(candidate="Klaro", source_clone_kib="17488", candidate_env_kib="0", install_duration_s="0.038 source bundle", start_or_fixture_duration_s="0.029", idle_cpu="N/A component", idle_ram_bytes="N/A component", max_rss_bytes="UNKNOWN", ports="none", storage_note="17.6 KiB bundled artifact"),
    dict(candidate="dedupe", source_clone_kib="1756", candidate_env_kib="237984", install_duration_s="36.910", start_or_fixture_duration_s="1.150 warm run", idle_cpu="N/A library", idle_ram_bytes="N/A library", max_rss_bytes="138051584", ports="none", storage_note="Isolated Python venv; peak memory footprint 106775128 bytes"),
    dict(candidate="OpenCATS", source_clone_kib="14504", candidate_env_kib="0", install_duration_s="NOT_RUN", start_or_fixture_duration_s="0.028 source fixture", idle_cpu="N/A no service", idle_ram_bytes="N/A no service", max_rss_bytes="UNKNOWN", ports="none", storage_note="Source only"),
    dict(candidate="Frappe HR", source_clone_kib="45132", candidate_env_kib="0", install_duration_s="NOT_RUN", start_or_fixture_duration_s="0.034 source fixture", idle_cpu="N/A no service", idle_ram_bytes="N/A no service", max_rss_bytes="UNKNOWN", ports="none", storage_note="Source only"),
]

contract_rows = [
    dict(candidate="Activepieces", connector_manifests="SOURCE: broad createPiece/auth catalog", token_isolation_without_real_tokens="SOURCE_ONLY", consent_suppression="NO", tenant_isolation="SOURCE_ONLY project/platform scoping", export_deletion="SOURCE_ONLY", human_owned_hiring_states="NO", evidence_level="source", integration_fit_proven="false", gaps="Core/EE split, server token encryption, tenant and deletion runtime"),
    dict(candidate="Nango", connector_manifests="PASS_CLI_FIXTURE", token_isolation_without_real_tokens="NOT_PROVEN candidate; independent fake-token harness PASS", consent_suppression="independent harness PASS; candidate not authoritative", tenant_isolation="SOURCE_ONLY connection/environment scoping; independent harness PASS", export_deletion="pre-connection deletion source; independent harness PASS", human_owned_hiring_states="NO", evidence_level="CLI fixture + independent loopback contract", integration_fit_proven="false", gaps="Start server/keystore with telemetry disabled and execute compiled action against mock"),
    dict(candidate="Twenty", connector_manifests="LIMITED/reference", token_isolation_without_real_tokens="NOT_RUN", consent_suppression="NO", tenant_isolation="SOURCE_ONLY workspace scoping", export_deletion="SOURCE_ONLY person/workspace lifecycle", human_owned_hiring_states="NO", evidence_level="source/license", integration_fit_proven="false", gaps="AGPL/commercial decision and runtime isolation/export/delete"),
    dict(candidate="Apache Unomi", connector_manifests="NO", token_isolation_without_real_tokens="NOT_APPLICABLE", consent_suppression="SOURCE_ONLY profile consent", tenant_isolation="NOT_PROVEN", export_deletion="SOURCE_ONLY profile deletion", human_owned_hiring_states="NO", evidence_level="source", integration_fit_proven="false", gaps="Java/Karaf/Elasticsearch runtime and tenant boundary"),
    dict(candidate="OpenFGA", connector_manifests="NO", token_isolation_without_real_tokens="NOT_APPLICABLE", consent_suppression="NO", tenant_isolation="SOURCE_ONLY authorization model capability", export_deletion="NO data ownership", human_owned_hiring_states="Can authorize, not own states", evidence_level="source/config; no start", integration_fit_proven="false", gaps="Run loopback model fixture with synthetic tenant tuples"),
    dict(candidate="Klaro", connector_manifests="NO", token_isolation_without_real_tokens="NOT_APPLICABLE", consent_suppression="PASS_COMPONENT_FIXTURE", tenant_isolation="NOT_NATIVE", export_deletion="PASS local consent reset only", human_owned_hiring_states="NO", evidence_level="executed component", integration_fit_proven="true (bounded component)", gaps="Server-side auditable consent/suppression ledger and multi-tenant policy"),
    dict(candidate="dedupe", connector_manifests="NO", token_isolation_without_real_tokens="NOT_APPLICABLE", consent_suppression="NO", tenant_isolation="PASS adapter pre-partition; NOT_NATIVE", export_deletion="PASS synthetic harness-owned state", human_owned_hiring_states="NO", evidence_level="installed library fixture", integration_fit_proven="true (bounded adapter)", gaps="Training/calibration, merge review and authorization outside library"),
    dict(candidate="OpenCATS", connector_manifests="NO", token_isolation_without_real_tokens="NOT_RUN", consent_suppression="NO", tenant_isolation="SOURCE_ONLY site_id patterns; NOT_PROVEN", export_deletion="PASS_SOURCE selected export; deletion permission source", human_owned_hiring_states="PASS_SOURCE permission gates/status history", evidence_level="executed JS + source assertions", integration_fit_proven="false", gaps="Legal provenance, PHP/database service, tenant and deletion runtime"),
    dict(candidate="Frappe HR", connector_manifests="NO", token_isolation_without_real_tokens="NOT_RUN", consent_suppression="NO", tenant_isolation="Framework site boundary; NOT_PROVEN", export_deletion="PASS_SOURCE role permissions", human_owned_hiring_states="PASS_SOURCE onboarding state/role contract", evidence_level="schema/controller fixture", integration_fit_proven="false", gaps="Frappe/ERPNext runtime, ATS workflow and data subject operations"),
]

cleanup_rows = [
    dict(scope="Mock connector HTTP service", path_or_resource="127.0.0.1:53176", created="yes", cleanup_action="server.shutdown/server_close and thread join in fixture finally block", status="CLEANED_VERIFIED", verification="Final lsof contains no 53176 listener"),
    dict(scope="Nango CLI global state", path_or_resource="/Users/vedantswami/Library/Preferences/nango-nodejs/config.json", created="yes (birth 2026-07-14T23:14:18+0530)", cleanup_action="fixtures/cleanup_nango_state.py removed exact 55-byte run-created file and empty parent", status="CLEANED_VERIFIED", verification="20260714T233239+0530-cleanup_nango_global_state.log"),
    dict(scope="Candidate services", path_or_resource="OpenFGA/Unomi/Twenty/Activepieces/OpenCATS/Frappe HR", created="no", cleanup_action="none", status="NOT_STARTED", verification="No candidate service port; final listener log"),
    dict(scope="Nango CLI processes", path_or_resource="CLI invocations", created="transient", cleanup_action="processes exited", status="CLEANED_VERIFIED", verification="No Nango candidate listener; residual Node PIDs are Hermes TypeScript LSP workers"),
    dict(scope="Disposable lab source/envs/artifacts", path_or_resource=str(LAB), created="yes", cleanup_action=f"After evidence review: remove disposable lab root {LAB}", status="RETAINED_FOR_REPRODUCTION", verification="final size 1917728 KiB; below 10 GiB lane cap"),
    dict(scope="OpenFGA release artifact", path_or_resource="artifacts/openfga_1.18.1_darwin_arm64.tar.gz and SBOM", created="yes", cleanup_action="Delete with retained lab root; artifact was never extracted/executed", status="RETAINED_NOT_RUN", verification="19040 KiB tarball; 212 KiB SBOM; below 2 GiB gate"),
    dict(scope="Shared package caches", path_or_resource="npm/pip/TypeScript user caches", created="possibly updated by installers/LSP", cleanup_action="not deleted because ownership predates/is shared beyond O06", status="DISCLOSED_NOT_CLEANED", verification="No credential/customer data intentionally written"),
    dict(scope="Nango anonymous telemetry", path_or_resource="Nango CLI /cli/telemetry endpoint", created="possible two fire-and-forget POST attempts", cleanup_action="irreversible egress; future runs must pass --no-telemetry", status="DISCLOSED_UNKNOWN_DELIVERY", verification="installed telemetry.service.js and CLI option source inspected; packet capture was not active"),
]


def write_csv(name: str, rows: list[dict[str, str]]) -> Path:
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path

csv_paths = [
    write_csv("candidate-inventory.csv", inventory_rows),
    write_csv("license-and-security.csv", license_rows),
    write_csv("deployment-smoke-results.csv", smoke_rows),
    write_csv("resource-profile.csv", resource_rows),
    write_csv("contract-fit.csv", contract_rows),
    write_csv("cleanup-manifest.csv", cleanup_rows),
]

process_rows = list(csv.DictReader((LAB / "logs/process-ledger.csv").open(encoding="utf-8")))
kind_counts = Counter(row["kind"] for row in process_rows)
repo_lines = "\n".join(f"- `{metadata[name]['repository']}@{metadata[name]['commit']}` — archive SHA-256 `{archive_hashes[name]}`" for name in metadata)
mandatory_files = [
    "AGENTS.md", "000_HOME.md", "05_Data/Current State/Dystopia Current Snapshot.md", "04_Logs/Daily/Daily Log - 2026-07-14.md",
    "02_Projects/Helixar World-Class Benchmark Program/00 Helixar World-Class Benchmark Program - Control Center.md",
    "02_Projects/Helixar World-Class Benchmark Program/02 Current Architecture Benchmark.md",
    "02_Projects/Helixar World-Class Benchmark Program/04 Cross-Packet Implementation Readiness Audit - 2026-07-14.md",
    "02_Projects/Helixar World-Class Benchmark Program/05 Hermes Parallel Architecture and Build Roadmap.md",
    "02_Projects/Helixar World-Class Benchmark Program/06 Folder and Evidence Use Guide.md",
    "02_Projects/Helixar World-Class Benchmark Program/Packets/R07 Mars-GTM Research and Architecture Packet.md",
    "02_Projects/Helixar World-Class Benchmark Program/Packets/R10 Mercury-Talent Research and Architecture Packet.md",
    "02_Projects/Helixar World-Class Benchmark Program/Prompts/O06 Connector, GTM and Talent OSS Lab Prompt.md",
]
context_lines = "\n".join(f"- `{DYSTOPIA / path}`" for path in mandatory_files)
ledger_lines = "\n".join(
    f"- `{DYSTOPIA / '05_Data/Helixar World-Class Benchmark Program' / f'R{i:02d} {name}' / filename}`"
    for i, name in enumerate(["Sol-Fleet", "Sol-Trust", "Terra-Authority", "Terra-Market", "Terra-Pain", "Luna-Creative", "Mars-GTM", "Mars-Measurement", "Mars-Economics", "Mercury-Talent"], 1)
    for filename in ("open-source-inventory.csv", "evidence-ledger.csv")
)
candidate_files = """- Activepieces: `LICENSE`, `packages/ee/LICENSE`, `SECURITY.md`, `package.json`, community piece/auth source matches.
- Nango: `LICENSE`, `LICENSE_SHORT`, `SECURITY.md`, `package.json`, `packages/cli/README.md`, `packages/cli/fixtures/nango-yaml/v2/valid/nango.yaml`, CLI/runtime auth/keystore/deletion source, installed `dist/services/telemetry.service.js`, `dist/state.js`, `dist/utils.js`.
- Twenty: `LICENSE`, `.github/SECURITY.md`, root manifests/Compose files, workspace/person/export/delete and telemetry source matches.
- Apache Unomi: `LICENSE`, `SECURITY.md`, `pom.xml`, runtime/Compose files, profile/consent/delete source matches.
- OpenFGA: `LICENSE`, `go.mod`, `cmd/run/flags.go`, Compose/config/telemetry source, fetched GitHub release metadata and SBOM.
- Klaro: `LICENSE`, `package.json`, `webpack.config.js`, `src/consent-manager.js`, `src/utils/cookies.js`.
- dedupe: `LICENSE`, `pyproject.toml`, `tests/test_dedupe.py`, installed `dedupe.clustering` implementation.
- OpenCATS: `LICENSE.md`, `composer.json`, `README.md`, `js/pipeline.js`, `ajax/getPipelineJobOrder.php`, `db/cats_schema.sql`.
- Frappe HR: `license.txt`, `pyproject.toml`, `SECURITY.md`, `hrms/hr/doctype/employee_onboarding/employee_onboarding.json`, `hrms/controllers/employee_boarding_controller.py`."""

report = f"""---
title: O06 Connector, GTM and Talent OSS Lab Report
date: 2026-07-14
status: Wave A complete with disclosed runtime and telemetry limitations
lanes: [R07 Mars-GTM, R10 Mercury-Talent]
lab_root: {LAB}
---

# O06 Connector, GTM and Talent OSS Lab Report

## 1. Executive verdict

**Adopt nothing wholesale.** Use **Klaro (`ADAPT`)** as a bounded client consent component and **dedupe (`ADAPT`)** as a tenant-prepartitioned entity-resolution library. Treat **Nango (`PARTNER`)** as the leading connector framework path because its CLI manifest/action workflow passed, but ELv2/all-rights-reserved boundaries, default CLI telemetry, and the untested server keystore require commercial/legal and security review. Advance **OpenFGA (`POC_MORE`)** in a separately approved toolchain because its Apache-2.0 authorization model is strategically strong, but this lane did not start it. Use OpenCATS and Frappe HR only as human-owned hiring contract references; neither produced a deployability proof.

No candidate is production-approved. Every candidate's production suitability remains **UNKNOWN**.

## 2. Boundary and lab conditions

- Wave A only: public source inspection, isolated installs, source/component fixtures and one disposable loopback mock.
- No implementation repository, credential, customer dataset, excluded Ultron source, CRM/ATS/finance system or live connector was accessed.
- Synthetic identities use `.invalid`; fake authorization values were `Synthetic token-*.invalid`.
- The only O06 HTTP service bound to `127.0.0.1` on ephemeral port `53176`, served 10 loopback requests, and shut down in its `finally` block.
- Total retained lab size: **1,917,728 KiB (~1.83 GiB)**, below the 10 GiB lane cap. Largest individual downloaded artifact: OpenFGA tarball **19,040 KiB**, below the 2 GiB gate.
- Host prerequisites: macOS 26.5.2 arm64; Node 24.13.0; npm 11.6.2; Python 3.13.0. Go, Java, PHP, Docker and pnpm were unavailable.
- Dystopia was used only for architecture/evidence outputs, never as a runtime database.

## 3. Candidate verdict matrix

| Candidate | Verdict | Executed evidence | Production gap |
|---|---|---|---|
| Activepieces | `POC_MORE` | Source/license/catalog only | Core/EE boundary, full stack, token and tenant runtime |
| Nango | `PARTNER` | CLI install/init/compile + manifest check; independent mock contract | ELv2, telemetry, server keystore and end-to-end action execution |
| Twenty | `REJECT_LICENSE` | Source/license only | AGPL/commercial split and multi-service runtime |
| Apache Unomi | `REJECT_OPERATIONS` | Source/license only | Java/Karaf/Elasticsearch operations and tenant proof |
| OpenFGA | `POC_MORE` | Source/config + release fetch only | Go absent; binary extraction approval-blocked; no auth model fixture |
| Klaro | `ADAPT` | Actual source component fixture PASS | Server-side consent receipt, policy and tenant authority |
| dedupe | `ADAPT` | Isolated venv + library fixture PASS | Tenant partition is adapter-owned; calibration/merge review |
| OpenCATS | `REJECT_LICENSE` | Actual JS + PHP/SQL source assertions PASS | Mixed license, PHP/database runtime and tenant proof |
| Frappe HR | `REJECT_OPERATIONS` | DocType/controller source fixture PASS | Frappe/ERPNext stack and full workflow proof |

Detailed row-level evidence is in the six CSVs beside this report.

## 4. Deterministic results

### Connector manifest and mock contract

- Nango `nango@0.71.0` installed 367 packages; `nango init` generated and compiled three example functions.
- A synthetic `mock-api/actions/upsertSyntheticContact.ts` action compiled with Nango. The generated `.nango/nango.json` included the `mock-api` provider/action and no credential value; no real connector action was sent.
- The independent loopback contract harness returned: health PASS, two fake-token tenant contexts, cross-tenant denial PASS, tenant-scoped export PASS, deletion PASS and suppression PASS. This proves the required **integration contract**, not Nango's server token isolation.
- Nango's server, database, KMS/keystore and real token lifecycle were not started. Therefore Nango integration fit is **not proven**.

### Consent and suppression

- Klaro's pinned `src/consent-manager.js` was bundled from source and executed.
- Default-denied analytics consent removed the synthetic analytics cookie, preserved required storage, persisted explicit acceptance, removed the cookie after withdrawal and deleted the consent record on reset.
- Klaro is not the authoritative server-side suppression ledger; adapt it only as UI/client enforcement.

### Identity and tenant isolation

- `dedupe` was installed from the pinned source clone into an isolated venv.
- The fixture executed `dedupe.clustering.cluster`, producing `(1,2)` inside `acme.invalid` and `(4,5)` inside `beta.invalid`, with zero cross-tenant candidate edges.
- Export then deletion of synthetic record `2` passed.
- This is an adapter contract: tenant prepartitioning must happen before dedupe candidate generation; dedupe is not an authorization boundary.

### Human-owned hiring states

- OpenCATS executed actual `js/pipeline.js` selection logic; source assertions found edit/delete permission gates, statuses `No Contact → Contacted → Interviewing → Offered → Placed`, and status-history schema. This is a source/UI/schema PASS, not a PHP service deployment.
- Frappe HR's Employee Onboarding DocType parsed; controller syntax compiled; statuses `Pending/In Process/Completed`, HR Manager submit/export and System Manager delete permissions passed. This is a schema/controller PASS, not a Frappe/ERPNext deployment.

### Authorization

- OpenFGA source/config/license fit is strong. A source build could not run because Go was absent. Release metadata, v1.18.1 Darwin arm64 tarball and SBOM were fetched, but extraction execution was approval-blocked. No service, health check or authorization tuple fixture ran; there is no OpenFGA PASS.

## 5. License and isolation analysis

- **Activepieces:** use only clearly non-enterprise paths after dependency tracing; `packages/ee` and the named server EE path carry the enterprise license.
- **Nango:** ELv2 plus `LICENSE_SHORT` all-rights-reserved notice means no unreviewed embedding/fork adoption. Prefer commercial partnership or a legal-approved bounded CLI workflow.
- **Twenty:** most code is AGPLv3 and enterprise-marked files are commercial. Reject source adoption in Wave A; a commercial partner decision is separate.
- **OpenCATS:** dual MPL-2.0 plus nonstandard CATS Public License 1.1a creates provenance/legal uncertainty. No code adoption.
- **Frappe HR:** GPL-3.0 is exact and known, but distribution obligations and heavy framework coupling remain.
- Apache Unomi/OpenFGA (Apache-2.0), Klaro (BSD-3) and dedupe (MIT) have clear selected-commit license files and hashes in `license-and-security.csv`.

## 6. Telemetry, egress and external writes

- Process ledger at report generation: `{len(process_rows)}` completed logged commands: `{kind_counts.get('public_network_fetch', 0)}` network-enabled fetch commands, `{kind_counts.get('loopback_request', 0)}` loopback fixture command, `{kind_counts.get('local_process', 0)}` local commands.
- Network-enabled command count is process-level, not individual HTTP request count: Git/npm/pip can issue multiple requests internally.
- Nango CLI source shows anonymous `/cli/telemetry` POSTs are enabled by default. `init` and `compile` were run without `--no-telemetry`, so **up to two anonymous telemetry delivery attempts may have occurred**; no packet capture was active and delivery is unknown. The created 55-byte Nango device-state file was detected by birth time and removed without exposing the identifier.
- External business-system writes: **0**. Live connector calls: **0**. CRM/ATS/finance mutations: **0**. Publish/send actions: **0**. Credentials/real tokens used: **0**.
- Loopback requests: **10**, all to `127.0.0.1:53176`; external requests from that fixture: **0**.

## 7. Exact repositories and files read

### Pinned repositories

{repo_lines}

### Mandatory context

{context_lines}

### R01–R10 inventories and ledgers

{ledger_lines}

### Candidate primary files/source surfaces

{candidate_files}

The complete intentional command/fetch ledger is `{LAB / 'logs/process-ledger.csv'}`; individual stdout/stderr receipts are under `{LAB / 'logs/commands'}`.

## 8. Commands/tests and real outputs

| Command/receipt | Real result |
|---|---|
| prerequisite probe | Go/Java/PHP/Docker/pnpm unavailable; Node/npm/Python available |
| nine `git clone --depth 1` commands | all exit 0; exact commits/archive hashes recorded |
| `npm install --prefix envs/nango-cli ... nango@0.71.0` | exit 0; 367 packages; deprecated inflight/glob warnings |
| `nango init fixtures/nango-smoke --auto-confirm` | exit 0; typecheck/build/generate PASS |
| `nango compile` | exit 0; four files built, artifacts generated |
| `nango_manifest_check.py` | PASS; mock action present; credential values 0; real calls 0 |
| `mock_connector_api_smoke.py` | PASS; 127.0.0.1 bind; 10 loopback requests; isolation/export/delete/suppression PASS |
| `pip install -e repos/dedupe` | exit 0 in isolated venv |
| `dedupe_tenant_fixture.py` | PASS; two same-tenant clusters, zero cross-tenant edges, delete PASS |
| Klaro esbuild + consent fixture | PASS; default deny, accept, withdraw/suppress and reset/delete |
| OpenCATS source fixture | PASS_SOURCE; executed JS and asserted permission/state/history source |
| Frappe HR source fixture | PASS_SOURCE; schema permissions/states and controller compile |
| OpenFGA release fetch | metadata/tarball/SBOM fetch exit 0; no extract/start; no PASS |
| cleanup Nango state | removed exact run-created 55-byte file and empty parent |
| final disk/listener probes | 1,917,728 KiB retained; no O06 mock/candidate listener remains |

## 9. Unresolved conflicts and required human decisions

1. Legal/commercial: approve or reject Nango ELv2 partnership; no source adoption by inference.
2. Legal: decide whether Twenty commercial licensing is worth evaluation; AGPL source embedding remains rejected.
3. Legal/engineering: authorize only traced Activepieces core paths or reject mixed-tree use.
4. Legal: OpenCATS file provenance under CATS Public License 1.1a; until resolved, no code adoption.
5. Architecture: choose whether connector execution is a dedicated fabric (Nango/Activepieces) or custom bounded adapters; this lab does not silently choose.
6. Security: authorize an OpenFGA POC in a loopback-only Go/container lane and define the tenant relation model.
7. Privacy: designate the authoritative consent/suppression/export/deletion ledger; Klaro is client enforcement only.
8. Talent operations: name the human owner and canonical state transitions before selecting an ATS/HR runtime.
9. Egress policy: require `--no-telemetry`/environment denial and packet-level egress capture in future connector tool evaluations.

## 10. Acceptance status

| Acceptance item | Status |
|---|---|
| All nine assigned candidates accounted for | PASS — nine rows in every candidate-level CSV |
| Primary repository, commit, archive source hash and license hash | PASS |
| Every PASS has command/fixture evidence | PASS — source/component/library scope is explicit |
| Unknown/unacceptable license means no code adoption | PASS |
| Connector framework smoke | PASS_CLI_FIXTURE — Nango compile/manifest; no server claim |
| Identity/authorization smoke | PASS_LIBRARY_FIXTURE — dedupe identity; OpenFGA authorization NOT_RUN |
| ATS/HR reference smoke | PASS_SOURCE_FIXTURE — OpenCATS and Frappe HR; no service claim |
| Mock API, fake tokens, tenant/export/delete/suppression | PASS independent contract harness |
| Loopback-only service and teardown | PASS |
| Download gates | PASS |
| No implementation repository/live business mutation | PASS |
| Network/process receipts | PASS_WITH_DISCLOSURE — intentional commands logged; Nango internal telemetry delivery not packet-observed |
| Production suitability | UNKNOWN for all candidates, as required |

## 11. Output map

- `{REPORT}`
""" + "\n".join(f"- `{path}`" for path in csv_paths) + f"\n- `{RECEIPT}`\n"
REPORT.write_text(report, encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

hash_lines = "\n".join(f"- `{path}` — SHA-256 `{sha(path)}`" for path in [REPORT, *csv_paths])
receipt = f"""---
title: 2026-07-14 O06 Connector GTM and Talent OSS Lab Run Receipt
date: 2026-07-14
status: complete-with-disclosures
---

# O06 Connector GTM and Talent OSS Lab Run Receipt — 2026-07-14

## Executive verdict

No wholesale adoption. `ADAPT` Klaro and dedupe as bounded components; `PARTNER` Nango subject to ELv2/commercial/security review; `POC_MORE` OpenFGA in an approved toolchain. OpenCATS/Frappe HR are contract references, not deployments. Production suitability is unknown for every candidate.

## Exact repositories read

{repo_lines}

## Exact Dystopia files read

{context_lines}

All 20 R01–R10 `open-source-inventory.csv` and `evidence-ledger.csv` paths are enumerated in the report.

## Exact files written and hashes

{hash_lines}
- `{RECEIPT}` — self-hash intentionally omitted

## Commands/tests and outputs

- Complete ledger: `{LAB / 'logs/process-ledger.csv'}` ({len(process_rows)} rows at report generation).
- Nango compile: exit 0, four files built, generated artifacts.
- Nango manifest: PASS, 0 credential values, 0 real connector calls.
- Loopback contract: PASS on `127.0.0.1:53176`, 10 requests, tenant isolation/export/delete/suppression PASS, then shutdown.
- dedupe: PASS, two same-tenant clusters, zero cross-tenant candidate edges; warm run 1.15 s, max RSS 138,051,584 bytes.
- Klaro: PASS, default deny/accept/withdraw cookie suppression/reset deletion.
- OpenCATS: PASS_SOURCE_FIXTURE; actual pipeline JavaScript executed; permission/status/history asserted.
- Frappe HR: PASS_SOURCE_FIXTURE; onboarding DocType and controller syntax validated.
- OpenFGA: NOT_RUN_PREREQUISITE; Go absent, release fetched, extraction approval-blocked, no service/fixture PASS.
- Final retained lab: 1,917,728 KiB; no O06 candidate/mock listener remains.

## Network and external-write counters

- Logged network-enabled command invocations: {kind_counts.get('public_network_fetch', 0)}.
- Logged loopback fixture invocations: {kind_counts.get('loopback_request', 0)}; HTTP requests inside fixture: 10.
- Logged local process invocations: {kind_counts.get('local_process', 0)}.
- Possible unobserved anonymous Nango telemetry attempts: up to 2; delivery unknown; run-created device state cleaned.
- Live connector calls: 0. Credentials/real tokens: 0. External business writes: 0. CRM/ATS/finance mutations: 0. Publish/send actions: 0.

## Cleanup

Mock server stopped; run-created Nango global state removed; no candidate service started. Lab retained for evidence review and is removable as a whole. Shared npm/pip/TypeScript caches were not deleted because ownership is not O06-exclusive. Residual Node processes with O06 files open were identified as Hermes TypeScript LSP workers, not candidate services.

## Unresolved human decisions

Nango commercial/legal path; Twenty AGPL/commercial path; Activepieces core/EE tracing; OpenCATS mixed-license provenance; OpenFGA POC authorization; authoritative consent/suppression ledger; human-owned hiring states; mandatory telemetry denial/packet capture for future labs.

## Deliverable acceptance

- Report: PASS present and hashed.
- candidate-inventory.csv: PASS, nine candidates.
- license-and-security.csv: PASS, nine candidates with exact license hashes.
- deployment-smoke-results.csv: PASS, nine candidates with scoped evidence.
- resource-profile.csv: PASS, nine candidates; unknowns explicit.
- contract-fit.csv: PASS, nine candidates.
- cleanup-manifest.csv: PASS, teardown/retention/egress states explicit.
- Receipt: PASS present; self-hash omitted by design.
"""
RECEIPT.write_text(receipt, encoding="utf-8")
print(json.dumps({"status": "PASS", "report": str(REPORT), "csvs": [str(path) for path in csv_paths], "receipt": str(RECEIPT), "candidate_rows": len(inventory_rows), "process_counts": dict(kind_counts)}, sort_keys=True))
