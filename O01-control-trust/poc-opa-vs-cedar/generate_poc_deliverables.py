#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

LAB = Path("/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust")
POC = LAB / "poc-opa-vs-cedar"
VAULT = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
ARCH = VAULT / "02_Projects/Helixar World-Class Benchmark Program/Architecture/O01A OPA vs Cedar Decision POC.md"
DATA = VAULT / "05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O01-control-trust/opa-vs-cedar"
RECEIPT = VAULT / "04_Logs/Runs/2026-07-15 - OPA vs Cedar Decision POC Run Receipt.md"
DATA.mkdir(parents=True, exist_ok=True)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)

results = json.loads((POC / "comparison-results.json").read_text())
matched_csv = (POC / "comparison-results.csv").read_text()
(DATA / "matched-cases.csv").write_text(matched_csv)
(DATA / "comparison-evidence.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")

provenance_fields = [
    "candidate", "tested_version", "source_repository", "source_commit", "package_source",
    "package_or_release_sha256", "binary_sha256", "binary_bytes", "license_spdx",
    "license_evidence", "license_sha256", "install_method", "source_inspected",
    "install_attempted", "cli_started", "deterministic_fixture_passed", "integration_fit_proven",
    "production_suitability",
]
provenance_rows = [
    {
        "candidate": "Open Policy Agent", "tested_version": "1.18.2",
        "source_repository": "https://github.com/open-policy-agent/opa",
        "source_commit": "e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297",
        "package_source": "official GitHub release opa_darwin_arm64_static",
        "package_or_release_sha256": "3ffa2af6a3b9ccff5d171d061d27990db5ad8cc5c10214c7eeeabc0f29ca11cf",
        "binary_sha256": "3ffa2af6a3b9ccff5d171d061d27990db5ad8cc5c10214c7eeeabc0f29ca11cf",
        "binary_bytes": "52799138", "license_spdx": "Apache-2.0",
        "license_evidence": str(POC / "provenance/opa-1.18.2-LICENSE"),
        "license_sha256": "6dc0e068dcf3a5bc8e054205b85b7720e1d49265bbc64bf515d2cf79197df69a",
        "install_method": "checksum-verified release binary retained from O01",
        "source_inspected": "true", "install_attempted": "true", "cli_started": "true",
        "deterministic_fixture_passed": "true", "integration_fit_proven": "false",
        "production_suitability": "UNKNOWN",
    },
    {
        "candidate": "Cedar", "tested_version": "4.11.2",
        "source_repository": "https://github.com/cedar-policy/cedar",
        "source_commit": "19c0e2591ba1d48b1cb43d43f35b64fdb3ac5e79",
        "package_source": "crates.io cedar-policy-cli 4.11.2",
        "package_or_release_sha256": "57d27ffdcc04aa965c4d0697fc492d5a95e232d44211400364e7dcfeef5bd770",
        "binary_sha256": "1423c6f295e7173f31c296a53917ec340adfed4d100b22134e481db30e802ae9",
        "binary_bytes": "15038624", "license_spdx": "Apache-2.0",
        "license_evidence": str(POC / "provenance/cedar-4.11.2-LICENSE"),
        "license_sha256": "7fb46adff9025f553b882b84ce593c37008d1e83019e4fdd6b21f8c800d0c485",
        "install_method": "isolated Rust 1.97.0 toolchain; cargo install --version 4.11.2 --locked",
        "source_inspected": "true", "install_attempted": "true", "cli_started": "true",
        "deterministic_fixture_passed": "true", "integration_fit_proven": "false",
        "production_suitability": "UNKNOWN",
    },
]
with (DATA / "provenance.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=provenance_fields)
    w.writeheader(); w.writerows(provenance_rows)

decision_fields = ["dimension", "opa", "cedar", "evidence_class", "winner", "decision_weight", "production_unknown"]
decision_rows = [
    ["matched authorization decisions", "6/6", "6/6", "LOCALLY_PROVEN_NETWORK_DENIED", "TIE", "high", "broader conformance corpus"],
    ["schema-aware policy typo rejection", "rejected undefined input.subject.tenent", "rejected tenent and suggested tenant", "LOCALLY_PROVEN", "TIE", "high", "CI activation workflow"],
    ["malformed runtime input", "failed closed as normal false decision", "rejected request with explicit typed diagnostic", "LOCALLY_PROVEN", "CEDAR", "high", "SDK path must preserve strict request validation"],
    ["deny precedence", "encoded inside allow conjunction; future rule discipline required", "separate forbid policy overrode satisfied permit", "LOCALLY_PROVEN", "CEDAR", "high", "erroring-forbid adversarial case not yet run"],
    ["authorization model", "general arbitrary JSON policy language", "purpose-built principal/action/resource/context model", "SOURCE_AND_DOC_OBSERVED", "CEDAR", "high", "full Helixar schema not frozen"],
    ["non-authorization policy breadth", "stronger for arbitrary compliance/config/data decisions", "intentionally narrower authorization scope", "DOCUMENTED", "OPA", "low for P0", "future cross-domain policy demand"],
    ["runtime topology", "mature CLI/server/sidecar/bundle/Wasm surfaces", "CLI and Rust SDK exercised only at CLI level", "SOURCE_AND_DOC_OBSERVED", "OPA", "high", "production Cedar adapter not exercised"],
    ["current Python service fit", "simple authenticated loopback sidecar or subprocess POC", "requires proven SDK/service/FFI adapter", "ARCHITECTURE_INFERENCE", "OPA", "high", "target implementation language/repository unresolved"],
    ["CLI wall time", "median 10.436 ms; p95 11.426 ms", "median 4.418 ms; p95 5.020 ms", "LOCALLY_PROVEN_STARTUP_INCLUDED", "CEDAR", "low", "not evaluator-only or concurrent throughput"],
    ["single fixture max RSS", "29868032 bytes", "9437184 bytes", "LOCALLY_PROVEN_ONE_RUN", "CEDAR", "low", "not daemon/embedded steady state"],
    ["decision observability", "arbitrary structured decisions plus established decision-log ecosystem", "determining policy IDs and typed diagnostics in CLI", "LOCALLY_PROVEN_PLUS_DOCUMENTED", "OPA", "medium", "production privacy and receipt integration"],
    ["supply chain/install", "checksum-verified official static binary", "checksum-verified crate built with isolated Rust toolchain", "LOCALLY_PROVEN", "OPA", "medium", "full dependency CVE and reproducible-build audit"],
    ["P0 recommendation", "fallback if Cedar adapter cannot pass gates quickly", "conditional ADAPT beneath Helixar authority ledger", "SYNTHESIS", "CEDAR_CONDITIONAL", "decisive", "human H0 and integration acceptance remain required"],
]
with (DATA / "decision-matrix.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(decision_fields); w.writerows(decision_rows)

report = f'''---
title: O01A OPA vs Cedar Decision POC
date: 2026-07-15
status: validated-conditional-recommendation-production-unknown
scope: R02 Sol-Trust follow-up to O01
lab_root: {LAB}
---

# O01A OPA vs Cedar Decision POC

## Executive verdict

**Choose Cedar 4.11.2 as the conditional P0 authorization evaluator beneath Helixar's own authority ledger. Keep OPA 1.18.2 as the operational fallback.**

This is `ADAPT`, not unconditional `ADOPT` and not H0 authorization. Cedar won the bounded POC because:

1. OPA and Cedar matched all six tenant/hash/approval fixtures under OS-level network denial.
2. Both rejected a misspelled policy field when schema-aware validation was enabled.
3. Cedar rejected missing/wrong-typed runtime context as an explicit request error; OPA failed closed but returned an ordinary `false`, making malformed input observationally identical to a normal denial.
4. Cedar's separate `forbid-revoked` policy overrode a satisfied permit. That deny precedence is structural; the tested Rego policy encoded revocation inside one allow conjunction and would require disciplined central deny composition as rules grow.
5. Cedar's constrained principal/action/resource/context model fits this narrow authorization boundary better than a general policy language.

OPA remains superior in deployment topology, current Python-service fit, operational ecosystem and decision-log infrastructure. If a production-shaped Cedar SDK/local-service adapter cannot pass the gates below quickly, choose OPA with strict caller-side runtime validation and centralized deny precedence.

**Neither engine owns approval truth, revocation, tenant authority, canonical receipts or final state transitions.** The Helixar ledger remains authoritative.

## Spike question and result

Given one synthetic tenant-scoped, hash-bound approval contract, when OPA and Cedar evaluate valid, denied, revoked, malformed and schema-invalid cases offline, which is the safer P0 policy evaluator?

**Verdict: VALIDATED WITH CONDITIONS — Cedar is the semantic winner; OPA is the operational fallback.**

## Real matched-case evidence

| Case | Expected | OPA | Cedar |
|---|---:|---:|---:|
| exact tenant/action/hash/valid approval | ALLOW | ALLOW | ALLOW |
| cross-tenant | DENY | DENY | DENY |
| target-hash mismatch | DENY | DENY | DENY |
| invalid approval | DENY | DENY | DENY |
| revoked approval | DENY | DENY | DENY (`forbid-revoked`) |
| wrong action | DENY | DENY | DENY |

Main fixture output:

```text
status=PASS
six_case_parity=true
opa_typo_rejected=true
cedar_typo_rejected=true
malformed_fail_closed=true
```

Raw evidence: `{POC / 'comparison-results.json'}`. Durable copy: `{DATA / 'comparison-evidence.json'}`.

## Malformed contract behavior

### Missing `approvalRevoked`

- OPA: exit `0`, output `false`.
- Cedar: exit `1`, `expected the record to have an attribute approvalRevoked, but it does not`.

### String instead of boolean

- OPA: exit `0`, output `false`.
- Cedar: exit `1`, context not valid for action `propose`.

Both paths enforce no action, but Cedar preserves `DENY` versus `ERROR`. The production Helixar adapter must use a three-state result: `ALLOW`, `DENY`, `ERROR`.

## Static policy validation

- OPA `check --strict --schema ... policy-typo.rego` rejected `input.subject.tenent` and named `tenant` as allowed.
- Cedar `validate --schema ... policy-typo.cedar` rejected `tenent` and suggested `tenant`.
- Valid policies passed both validators.

## Bounded resource evidence

| Measure | OPA | Cedar |
|---|---:|---:|
| 50-process CLI median | 10.436 ms | 4.418 ms |
| 50-process CLI p95 | 11.426 ms | 5.020 ms |
| Single final allow max RSS | 29,868,032 bytes | 9,437,184 bytes |
| Runtime artifact | 52,799,138 bytes | 15,038,624 bytes |

These include CLI startup/parsing and are not evaluator-only, warm, concurrent or daemon benchmarks. They do not drive the architecture decision.

## Provenance and license

| Engine | Tested version | Exact source | Package/release integrity | License |
|---|---|---|---|---|
| OPA | 1.18.2 | `e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297` | static binary SHA-256 `3ffa2af6...1cf` matched official checksum | Apache-2.0; exact license SHA-256 `6dc0e068...f69a` |
| Cedar | 4.11.2 | `19c0e2591ba1d48b1cb43d43f35b64fdb3ac5e79` | crate SHA-256 `57d27ffd...770` matched crates.io; built `--locked` | Apache-2.0; exact license SHA-256 `7fb46adf...c485` |

Full hashes: `{DATA / 'provenance.csv'}`.

## Decision matrix

The full machine-readable comparison is `{DATA / 'decision-matrix.csv'}`.

### Cedar advantages

- Purpose-built authorization model and narrower review surface.
- Default deny plus explicit forbid-overrides-permit composition.
- Typed action/entity/context schema with explicit malformed-request diagnostics in the exercised CLI path.
- Determining policy IDs visible in verbose authorization output.
- Smaller/faster bounded CLI artifact in this POC.

### OPA advantages

- More mature operational topologies: server/sidecar, bundles and established management/decision-log patterns.
- Natural fit for Python/FastAPI through a local service boundary.
- Arbitrary structured data and arbitrary structured decision documents.
- Existing checksum-verified binary already exercised before this follow-up.

## Critical Cedar safety condition

Cedar documents skip-on-error policy semantics: a policy that errors can be omitted from the authorization calculation. Therefore Helixar must reject an `ALLOW` if any relevant evaluation error/diagnostic exists. A malformed request, evaluation diagnostic, missing entity, stale policy/schema revision, timeout, transport failure or engine failure becomes `ERROR` and enforces no action.

## Required production gate before Cedar can enforce P0

1. No production CLI subprocess architecture; prove a pinned embedded SDK or authenticated loopback-only local service.
2. Strict schema-aware request/entity parsing on every call.
3. Three-state Helixar result: `ALLOW`, `DENY`, `ERROR`.
4. Reject any allow carrying evaluation diagnostics.
5. Atomic policy+schema activation; bind both hashes and versions into the canonical ledger receipt.
6. Keep Cedar entity/request formats transient behind a Helixar-owned port.
7. Add adversarial tests: erroring forbid plus satisfied permit; unknown action/entity; missing/null/extra/wrong-type fields; conflicting permits/forbids; stale revisions; crash/timeout; Unicode and oversized/deep inputs; revocation race; property test `no allow unless every invariant holds`.
8. Run concurrent warm latency, restart, cache invalidation, rollback, failure and observability/privacy tests.
9. Complete dependency/CVE and reproducible-build review.
10. Obtain human H0 approval after the adapter and corpus pass. This POC is not approval.

## OPA fallback gate

If Cedar's adapter cannot pass those gates within P0, choose OPA only with:

- caller-side Pydantic/JSON-Schema runtime validation;
- one normalized authorization endpoint;
- centralized `allow AND NOT deny` composition;
- undefined/runtime failures mapped to `ERROR`;
- pinned bundle revision and policy/schema/input hashes in receipts;
- masked decision logs.

## Production unknowns and non-claims

Not proven: implementation integration, embedded/daemon behavior, concurrency, crash recovery, policy distribution/rollback, full adversarial correctness, CVE posture, authorization/enforcement atomicity, revocation races, production observability/privacy, or operator readiness. The six-case offline POC proves bounded semantics only.

## Primary evidence

- OPA Rego policy language: https://www.openpolicyagent.org/docs/latest/policy-language/
- Cedar security and semantics: https://docs.cedarpolicy.com/other/security.html
- Cedar 4.11.2 crates metadata/checksum: https://crates.io/api/v1/crates/cedar-policy-cli/4.11.2
- Existing O01 report: [[02_Projects/Helixar World-Class Benchmark Program/Architecture/O01 Control Plane, Trust and Observability OSS Lab Report|O01 Control Plane, Trust and Observability OSS Lab Report]]
- Run receipt: [[04_Logs/Runs/2026-07-15 - OPA vs Cedar Decision POC Run Receipt|2026-07-15 OPA vs Cedar Decision POC Run Receipt]]
'''
ARCH.write_text(report)

receipt = f'''---
title: 2026-07-15 OPA vs Cedar Decision POC Run Receipt
date: 2026-07-15
started_at_utc: 2026-07-14T18:02:21.421389+00:00
status: pre-final-validation
scope: O01A follow-up for R02 Sol-Trust
---

# OPA vs Cedar Decision POC — Run Receipt

## Verdict

Conditional recommendation: **Cedar 4.11.2 `ADAPT` for P0 authorization beneath the Helixar authority ledger; OPA 1.18.2 is the fallback if the Cedar production adapter cannot pass the stated gates.** No H0 authority or implementation work was granted.

## Exact required context read

- `{VAULT / 'AGENTS.md'}`
- `{VAULT / '000_HOME.md'}`
- `{VAULT / '05_Data/Current State/Dystopia Current Snapshot.md'}`
- `{VAULT / '04_Logs/Daily/Daily Log - 2026-07-14.md'}`
- `{VAULT / '02_Projects/Helixar World-Class Benchmark Program/Architecture/O01 Control Plane, Trust and Observability OSS Lab Report.md'}`
- `{LAB / 'source-metadata.json'}`
- `{POC / 'cases.json'}`
- `{POC / 'comparison-results.json'}`
- exact OPA/Cedar policy, schema, source-commit license and package provenance files under `{POC}`

## Exact durable files written

- `{ARCH}`
- `{DATA / 'matched-cases.csv'}`
- `{DATA / 'comparison-evidence.json'}`
- `{DATA / 'provenance.csv'}`
- `{DATA / 'decision-matrix.csv'}`
- `{RECEIPT}`
- detached final hashes: `{DATA / 'sha256-manifest.txt'}`
- final validation: `{DATA / 'validation-result.json'}`

The O01 report, current snapshot and 2026-07-15 daily log receive link/status updates after this receipt is generated; they are validated in the final gate.

## Install and real test outputs

- Cedar isolated install: `cargo install cedar-policy-cli --version 4.11.2 --locked`; real output: `Installed package cedar-policy-cli v4.11.2 (executable cedar)`.
- Cedar version: `cedar-policy-cli 4.11.2`.
- Cedar policy validation: `policy set validation passed; no errors or warnings`.
- Main comparison under `sandbox-exec ... deny network*`: `status PASS`; all six acceptance booleans true.
- OPA typo: `rego_type_error: undefined ref: input.subject.tenent`.
- Cedar typo: `attribute tenent ... not found`; help: `did you mean tenant?`.
- Matched cases: 6/6 expected parity.
- Cedar crate checksum: `57d27ffdcc04aa965c4d0697fc492d5a95e232d44211400364e7dcfeef5bd770` matched crates.io.
- OPA release binary checksum: `3ffa2af6a3b9ccff5d171d061d27990db5ad8cc5c10214c7eeeabc0f29ca11cf` matched official checksum.

## Activity counters

Counter scope begins at the first follow-up lab record `2026-07-14T18:02:21.421389+00:00`.

- Logged follow-up lab commands before deliverable generation: 15 (7 network-capable, 8 local).
- Logged failed network commands: 2 exploratory release-lookup attempts.
- Additional timed-out Git partial-checkout restore: 1 network-capable attempt; no implementation repository involved.
- Parent web research tools: 5 calls.
- Independent review subagent web research tools: 11 calls.
- Total public-network tool/command invocations disclosed before finalization: 24.
- Package-manager internal HTTP requests: not packet-captured; network count is invocation-level, not transaction-level.
- External/business writes: 0.
- Credentials/customer data: 0.
- Implementation-repository writes: 0.
- Dystopia runtime state: 0; Dystopia receives derivative evidence only.
- Lab bytes after build: 4,001,904,561; below 10 GB lane limit; no artifact over 2 GB.

## Human decisions and blockers

- Human H0 must approve the engine and adapter after production-shaped gates.
- Choose exact Cedar integration topology and owning repository; neither exists in this POC.
- Approve fail-closed error semantics, canonical receipt fields, policy/schema activation and rollback.
- If the Cedar adapter cannot be proven quickly, invoke the documented OPA fallback gate.

## Acceptance before final gate

- Exact OPA/Cedar versions and source/license provenance: PASS.
- One shared contract and six matched cases: PASS.
- Static schema typo rejection: PASS both.
- Runtime malformed-input comparison: PASS and difference recorded.
- Network-denied final fixture: PASS.
- Integration fit: NOT_PROVEN.
- Production suitability: UNKNOWN.
- Human H0: NOT_GRANTED.

Final structural, hash, source-link, process/listener and output validation is written after this receipt exists.
'''
RECEIPT.write_text(receipt)
print(json.dumps({"status": "generated", "files": [str(ARCH), str(DATA / 'matched-cases.csv'), str(DATA / 'comparison-evidence.json'), str(DATA / 'provenance.csv'), str(DATA / 'decision-matrix.csv'), str(RECEIPT)]}, indent=2))
