#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

LAB=Path('/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust')
DYS=Path('/Users/vedantswami/Projects/Dystopia/Dystopia')
OUT=DYS/'05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O01-control-trust'
REPORT=DYS/'02_Projects/Helixar World-Class Benchmark Program/Architecture/O01 Control Plane, Trust and Observability OSS Lab Report.md'
OUT.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
summary=json.loads((LAB/'lab-summary.json').read_text())
meta={x['candidate']:x for x in summary['candidates']}
records=[json.loads(x) for x in (LAB/'logs/process-network.jsonl').read_text().splitlines() if x.strip()]

def last_duration(name, needle, passed=True):
    vals=[r['duration_seconds'] for r in records if r['candidate']==name and needle in r['command'] and (r['exit_code']==0 if passed else r['exit_code']!=0)]
    return vals[-1] if vals else ''

def write_csv(name, fields, rows):
    path=OUT/name
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    return path

specs={
 'temporal':dict(label='Temporal',category='orchestration/durability',lanes='R01;R02',license='MIT',version='source snapshot',classification='POC_MORE',relevance='Durable workflow benchmark for long-running, replayable control-plane jobs.',authority='Must remain below the Helixar authority ledger; never the approval authority.',pause='Durable workflow history with signals/updates/timers; operational proof not run.',idem='Deterministic workflow replay plus workflow/activity IDs; external side effects still require idempotency keys.',data='Workflow histories, task queues, namespaces, activities, events.',ops='Persistent service plus database and workers; highest operational weight in this set.',replace='LOW_MEDIUM: history and workflow API coupling are substantial.',mapping='Benchmark for durable execution after the simpler ledger contract is stable.',fit='POC_MORE',unresolved='Human decision: when scale justifies a durable server; no local deployment proof.'),
 'langgraph':dict(label='LangGraph',category='orchestration/durability',lanes='R01;R02',license='MIT',version='1.2.9 from selected source',classification='ADAPT',relevance='In-process specialist graph with explicit checkpointed interrupt/resume.',authority='Specialist execution only; cannot own approvals, policy, tenant authority, or canonical receipts.',pause='PROVEN_BOUNDED: interrupt persisted in MemorySaver and resumed with Command(resume=True).',idem='Thread/checkpoint continuity is proven; external effect idempotency is not automatic.',data='Typed graph state, checkpoints, thread_id, pending node.',ops='Python library; production requires an approved durable checkpointer and lifecycle ownership.',replace='HIGH behind a Helixar specialist-runtime port.',mapping='Fits specialist execution adapter beneath fleet command and authority ledger.',fit='ADAPT',unresolved='Durable database checkpointer, crash replay and multi-process behavior not tested.'),
 'trigger-dev':dict(label='Trigger.dev',category='orchestration/durability',lanes='R01;R02',license='Apache-2.0',version='source snapshot',classification='POC_MORE',relevance='Developer-oriented durable background jobs with waits, retries and operational UI.',authority='Job runner only; must not become canonical control-plane authority.',pause='Documented waits/checkpoints; not locally proven in this lane.',idem='Retry semantics exist; business side effects still require Helixar idempotency keys.',data='Runs, tasks, attempts, queues, schedules, checkpoints.',ops='Self-hosted TypeScript platform with worker/queue/storage dependencies; no smoke deployment.',replace='MEDIUM if isolated behind job-runner port.',mapping='Possible worker execution plane, not P0 authority.',fit='POC_MORE',unresolved='Self-host topology, resource profile and failure recovery not tested.'),
 'prefect':dict(label='Prefect',category='orchestration/durability',lanes='R01;R02',license='Apache-2.0',version='source snapshot',classification='POC_MORE',relevance='Dataflow orchestration candidate, most relevant for scheduled ingestion and batch jobs.',authority='Ingestion scheduler only; never approval or policy authority.',pause='Flow states support pause/suspend patterns; not locally proven.',idem='Retries/caching help but do not provide business-effect idempotency.',data='Flows, task runs, deployments, work pools, states, artifacts.',ops='Server/API/database plus workers for self-hosted use; no deployment attempted.',replace='MEDIUM_HIGH behind an ingestion-scheduler port.',mapping='Possible future ingestion plane for R03/R06, weak P0 control-plane fit.',fit='POC_MORE',unresolved='No proof that it adds value over Hermes cron plus ledger at current scale.'),
 'opa':dict(label='Open Policy Agent',category='policy/authorization',lanes='R02',license='Apache-2.0',version='v1.18.2 binary; commit e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297',classification='POC_MORE',relevance='General-purpose deterministic policy evaluation with data/input separation and strong tooling.',authority='Policy decision point only; enforcement and authoritative receipts remain Helixar-owned.',pause='N/A; stateless decision evaluation.',idem='Deterministic for fixed policy/data/input; policy bundle/version must be receipt-bound.',data='Rego modules, data documents, query input/output and bundles.',ops='Single CLI/binary or loopback service; fixture used CLI only.',replace='HIGH behind an allow/deny/reasons/obligations policy-engine port.',mapping='Best technically proven O01 policy candidate, but OPA-vs-Cedar remains H0.',fit='POC_MORE',unresolved='Human H0 selection against Cedar; service auth/bundle lifecycle not tested.'),
 'cedar':dict(label='Cedar',category='policy/authorization',lanes='R02',license='Apache-2.0',version='source snapshot',classification='POC_MORE',relevance='Typed authorization policy language and evaluator suitable for embedded enforcement.',authority='Policy decision component only; Helixar remains enforcement and receipt authority.',pause='N/A; stateless authorization evaluation.',idem='Deterministic for fixed schema, entities, policies and request.',data='Schema, entities, policies, principal/action/resource/context request.',ops='Rust library/CLI pattern; Rust toolchain was absent, so install was not attempted.',replace='HIGH if normalized behind the Helixar policy port.',mapping='OPA alternative for H0; stronger typed authorization model, narrower general policy surface.',fit='POC_MORE',unresolved='Human H0 selection and a future exact-version fixture on a prepared Rust lane.'),
 'openfga':dict(label='OpenFGA',category='policy/authorization',lanes='R02',license='Apache-2.0',version='source snapshot',classification='REJECT_FIT',relevance='Relationship-based authorization for object graphs, not a general approval/policy engine.',authority='Could answer relationship checks only; cannot own Helixar approval validity.',pause='N/A.',idem='Deterministic tuple/model checks; tuple-write lifecycle adds state.',data='Authorization models, relationship tuples, checks and stores.',ops='Persistent network service plus database; no local deployment.',replace='MEDIUM behind a relationship-authorization port.',mapping='Potential later tenant/resource sharing subsystem, not P0 trust enforcement.',fit='REJECT_FIT',unresolved='Revisit only if Zanzibar-style relationship requirements become concrete.'),
 'opentelemetry':dict(label='OpenTelemetry',category='telemetry',lanes='R01;R02',license='Apache-2.0',version='spec commit plus Python SDK 1.43.0',classification='ADOPT',relevance='Vendor-neutral trace/metric/log transport and context standard.',authority='Observability only; telemetry is evidence, never authority state.',pause='N/A.',idem='Export can duplicate; receipt/event IDs and downstream deduplication are required.',data='Resources, spans, events, attributes, metrics and logs.',ops='In-process SDK proven with in-memory exporter; collector deployment not tested.',replace='HIGH by design through protocol/exporter interoperability.',mapping='Adopt as transport/interface; preserve canonical evidence in Helixar-owned receipts.',fit='ADOPT',unresolved='Collector topology, retention, redaction and sampling require later production design.'),
 'openinference':dict(label='OpenInference',category='telemetry',lanes='R02',license='Apache-2.0',version='source snapshot',classification='ADAPT',relevance='LLM/agent semantic conventions layered on OpenTelemetry.',authority='Observability annotations only; prompt/tool content must be governed and redacted.',pause='N/A.',idem='Inherits telemetry duplicate behavior; IDs needed.',data='Spans and attributes for models, tools, retrieval and agents.',ops='Convention/instrumentation packages; no separate service and no local fixture.',replace='HIGH if mapped through an internal semantic adapter.',mapping='Selective mapping for agent spans; do not make vendor-specific fields canonical.',fit='ADAPT',unresolved='Field-level privacy allowlist and compatibility with the final event envelope.'),
 'promptfoo':dict(label='Promptfoo',category='eval/observability/security',lanes='R02',license='MIT',version='0.121.19',classification='ADAPT',relevance='Portable CLI evaluation and red-team assertions with structured artifacts.',authority='Evaluation evidence only; cannot approve production actions.',pause='N/A for the tested CLI run.',idem='Deterministic echo fixture; production runs need dataset/config/source hashes.',data='YAML config, providers, prompts, tests, assertions and JSON results.',ops='Node CLI; 714 packages installed in lab, 825 production/optional/peer packages audited.',replace='HIGH through exported fixtures and normalized EvalReport contract.',mapping='Useful eval-runner adapter under R02, with remote generation and telemetry disabled.',fit='ADAPT',unresolved='Large dependency footprint; production datasets/providers not tested.'),
 'inspect-ai':dict(label='Inspect AI',category='eval/observability/security',lanes='R02',license='MIT',version='source snapshot',classification='POC_MORE',relevance='Structured Python evaluation framework with tasks, solvers, scorers and logs.',authority='Evaluation only.',pause='Task-level execution semantics; not tested.',idem='Requires pinned model, dataset, scorer and task configuration.',data='Tasks, samples, solvers, scorers, transcripts and logs.',ops='Python package; install not attempted to preserve lane time/download budget.',replace='HIGH behind EvalReport normalization.',mapping='Strong alternative/companion to Promptfoo for code-native evals.',fit='POC_MORE',unresolved='Direct deterministic fixture and artifact contract comparison with Promptfoo.'),
 'langfuse':dict(label='Langfuse',category='eval/observability/security',lanes='R02',license='MIT core; separate ee/LICENSE boundary',version='source snapshot',classification='POC_MORE',relevance='Self-hosted tracing, prompt and evaluation UI with an open-core boundary.',authority='Viewer/analytics only; must not become canonical evidence or approval state.',pause='N/A.',idem='Trace ingestion can duplicate; stable trace/observation IDs required.',data='Traces, observations, scores, prompts and datasets in application-specific stores.',ops='Multi-service self-host stack; not deployed in this lane.',replace='MEDIUM: APIs/export reduce risk, but UI/schema/store coupling remains.',mapping='Optional viewer fed by OpenTelemetry/Helixar evidence after P0 contracts exist.',fit='POC_MORE',unresolved='Core/EE feature boundary, local stack resources and export fidelity.'),
 'phoenix':dict(label='Phoenix',category='eval/observability/security',lanes='R01;R02',license='Elastic-2.0',version='source snapshot',classification='REJECT_LICENSE',relevance='Strong LLM tracing/evaluation viewer and OpenTelemetry integrations.',authority='Viewer/evaluation only.',pause='N/A.',idem='Stable trace/span IDs required for ingestion.',data='Projects, traces, spans, datasets, experiments and annotations.',ops='Python/server application; not installed or started.',replace='MEDIUM through OTel and exported artifacts.',mapping='Architecturally relevant optional viewer, but selected commit is source-available, not OSI open source.',fit='REJECT_LICENSE',unresolved='Legal decision could permit use; no code adoption under this OSS lane.'),
 'giskard':dict(label='Giskard',category='eval/observability/security',lanes='R02',license='Apache-2.0',version='source snapshot',classification='POC_MORE',relevance='LLM vulnerability scanning/evaluation with migration signals toward newer product surfaces.',authority='Testing evidence only.',pause='N/A.',idem='Requires pinned scanner version, model adapter and dataset.',data='Models, datasets, scan findings, tests and reports.',ops='Python/application dependencies; not installed.',replace='MEDIUM_HIGH with normalized findings.',mapping='Possible offline red-team scanner after R02 fixture contracts stabilize.',fit='POC_MORE',unresolved='Project direction/migration, deterministic offline coverage and resource footprint.'),
 'pyrit':dict(label='PyRIT',category='eval/observability/security',lanes='R02',license='MIT',version='source snapshot',classification='POC_MORE',relevance='Security-oriented orchestration for adversarial AI testing.',authority='Security-test evidence only; must be isolated from live targets by approval.',pause='Campaign orchestration semantics; not tested.',idem='Campaign reproducibility requires pinned prompts, converters, scorers and target.',data='Prompts, conversations, targets, scorers, converters and memory.',ops='Python framework; not installed and no outbound target exercised.',replace='HIGH behind a RedTeamFinding contract.',mapping='Future adversarial lane using synthetic/local targets only.',fit='POC_MORE',unresolved='Offline target fixture, egress controls and human authorization workflow.'),
 'garak':dict(label='garak',category='eval/observability/security',lanes='R02',license='Apache-2.0',version='source snapshot',classification='POC_MORE',relevance='Probe-based LLM vulnerability scanner with detector/report ecosystem.',authority='Security findings only.',pause='N/A.',idem='Reproducibility depends on pinned generator, probes, detectors and seeds.',data='Generators, probes, attempts, detectors, scores and reports.',ops='Python CLI; not installed and no model/target downloaded.',replace='HIGH through normalized finding exports.',mapping='Candidate for later offline security packs against approved local targets.',fit='POC_MORE',unresolved='Deterministic no-model fixture, resource profile and finding normalization.'),
 'presidio':dict(label='Presidio',category='eval/observability/security',lanes='R02',license='MIT',version='2.2.363 analyzer/anonymizer from source',classification='ADAPT',relevance='PII detection/anonymization guard for ingress and telemetry payloads.',authority='Redaction assist only; not a guarantee and not policy authority.',pause='N/A.',idem='Deterministic for fixed recognizers/model/version; offsets and replacement policy must be pinned.',data='Recognizer results with entity type, offsets, scores and anonymized text.',ops='Python libraries; default AnalyzerEngine unexpectedly downloaded a 400.7 MB spaCy model and peak RSS reached 690.6 MB.',replace='HIGH behind a RedactionResult port and layered fallback rules.',mapping='Adapt as defense-in-depth before evidence export; keep regex/rule fallback and quality evals.',fit='ADAPT',unresolved='Explicit no-auto-download NLP config, recall evaluation and lower-memory packaging.'),
}

smoked={'langgraph','opa','opentelemetry','promptfoo','presidio'}
started={'opa','promptfoo'}
inv=[]
for key,s in specs.items():
    m=meta[key]; commit=m['commit']; ref=m['default_branch_ref']
    if key=='opa': commit='e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297'; ref='v1.18.2'
    inv.append({'candidate_id':key,'candidate':s['label'],'category':s['category'],'source_lane_ids':s['lanes'],'repository_url':m['repository'],'selected_ref':ref,'selected_commit':commit,'source_hash_type':'git_commit_sha1','source_hash':commit,'source_inspected':'true','inspected_files':';'.join(m['inspected_paths']),'install_attempted':str(key in smoked).lower(),'service_or_cli_started':str(key in started).lower(),'library_fixture_executed':str(key in smoked and key not in started).lower(),'deterministic_fixture_passed':str(key in smoked).lower(),'integration_fit_proven':'false','production_suitability_unknown':'true','classification':s['classification'],'selected_component_version':s['version'],'relevance':s['relevance'],'notes':s['unresolved']})
write_csv('candidate-inventory.csv',list(inv[0]),inv)

lic=[]
for key,s in specs.items():
    m=meta[key]; commit='e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297' if key=='opa' else m['commit']
    dep='NOT_RUN_CVE_SCAN'
    vuln='UNKNOWN'
    sec='Exact repository license inspected; production security review not performed.'
    if key in {'langgraph','opentelemetry','presidio'}: dep='PASS_DEPENDENCY_CONSISTENCY; NOT_RUN_CVE_SCAN'
    if key=='promptfoo': dep='PASS npm audit --omit=dev at 0.121.19'; vuln='0 across info/low/moderate/high/critical; 825 total dependency entries reported'; sec='Runtime fixture passed under network-deny sandbox; large transitive dependency surface remains.'
    if key=='opa': dep='PASS release SHA-256 and source-tag commit match'; vuln='UNKNOWN'; sec='Downloaded v1.18.2 static binary checksum verified; three policy tests passed.'
    if key=='presidio': sec='Unexpected runtime model download recorded; project warns automated detection is not guaranteed to find all sensitive information.'
    boundary='NONE_OBSERVED'
    adoption='true'
    if key=='langfuse': boundary='ee/LICENSE separate from MIT core; enterprise files excluded from adoption'; adoption='core_only'
    if key=='phoenix': boundary='Elastic License 2.0 restrictions; legal approval required'; adoption='false_pending_legal'
    lic.append({'candidate_id':key,'candidate':s['label'],'repository_url':m['repository'],'selected_commit':commit,'license_path':'LICENSE' if key!='opa' else 'LICENSE at v1.18.2','spdx_or_exact_license':s['license'],'license_sha256':m['license_sha256'],'code_adoption_allowed':adoption,'secondary_license_boundary':boundary,'dependency_security_check':dep,'vulnerability_result':vuln,'security_observation':sec,'production_security_suitability':'UNKNOWN','license_classification':s['classification']})
write_csv('license-and-security.csv',list(lic[0]),lic)

notrun_reason={k:specs[k]['unresolved'] for k in specs if k not in smoked}
smokes=[]
def add_smoke(**kw): smokes.append(kw)
add_smoke(smoke_id='langgraph-01',candidate_id='langgraph',stage='deterministic_fixture',status='PASS',source_inspected='true',install_attempted='true',service_or_cli_started='false',library_fixture_executed='true',fixture_passed='true',integration_fit_proven='false',command='sandbox-exec -p (version 1)(allow default)(deny network*) envs/langgraph/.venv/bin/python fixtures/langgraph_fixture.py',expected='interrupt blocks side effect; resume produces value=2 and one synthetic effect',real_output='PASS langgraph_interrupt_resume value=2 effects=1 pre_resume_effects=0',duration_seconds=last_duration('langgraph','langgraph_fixture.py'),network_runtime='DENIED_BY_SANDBOX_AND_PASS',ports='NONE',evidence=str(LAB/'logs/langgraph.log'))
add_smoke(smoke_id='opa-01',candidate_id='opa',stage='deterministic_fixture',status='PASS',source_inspected='true',install_attempted='true',service_or_cli_started='true',library_fixture_executed='false',fixture_passed='true',integration_fit_proven='false',command='envs/opa/opa test fixtures/opa/policy.rego fixtures/opa/policy_test.rego -v',expected='same-tenant exact-hash allow; cross-tenant and hash-mismatch deny',real_output='PASS: 3/3; allow eval true; deny eval false',duration_seconds=last_duration('opa','opa test'),network_runtime='DENIED_BY_SANDBOX_AND_PASS',ports='NONE',evidence=str(LAB/'logs/opa.log'))
add_smoke(smoke_id='opentelemetry-01',candidate_id='opentelemetry',stage='deterministic_fixture',status='PASS',source_inspected='true',install_attempted='true',service_or_cli_started='false',library_fixture_executed='true',fixture_passed='true',integration_fit_proven='false',command='sandbox-exec -p (version 1)(allow default)(deny network*) envs/opentelemetry/.venv/bin/python fixtures/opentelemetry_fixture.py',expected='one in-memory span; no prompt/completion/tool-argument attributes',real_output='PASS otel_in_memory_export spans=1 sensitive_content_attributes=0',duration_seconds=last_duration('opentelemetry','opentelemetry_fixture.py'),network_runtime='DENIED_BY_SANDBOX_AND_PASS',ports='NONE',evidence=str(LAB/'logs/opentelemetry.log'))
add_smoke(smoke_id='promptfoo-01',candidate_id='promptfoo',stage='deterministic_fixture',status='PASS',source_inspected='true',install_attempted='true',service_or_cli_started='true',library_fixture_executed='false',fixture_passed='true',integration_fit_proven='false',command='sandbox-exec -p (version 1)(allow default)(deny network*) env PROMPTFOO_DISABLE_TELEMETRY=true PROMPTFOO_DISABLE_REMOTE_GENERATION=true promptfoo eval -c promptfooconfig.yaml --no-cache',expected='1/1 test pass; two assertions pass; no model requests',real_output='1 passed; 0 failed; 0 errors; tokenUsage total=0; result-sandbox.json written',duration_seconds=last_duration('promptfoo','result-sandbox.json'),network_runtime='DENIED_BY_SANDBOX_AND_PASS',ports='NONE',evidence=str(LAB/'logs/promptfoo.log'))
add_smoke(smoke_id='presidio-01',candidate_id='presidio',stage='first_fixture',status='FAIL',source_inspected='true',install_attempted='true',service_or_cli_started='false',library_fixture_executed='true',fixture_passed='false',integration_fit_proven='false',command='envs/presidio/.venv/bin/python fixtures/presidio_fixture.py',expected='custom recognizer redacts .invalid email without network',real_output='Unexpected 400.7 MB en_core_web_lg download; assertion failed',duration_seconds='78.50',network_runtime='UNPLANNED_EGRESS_RECORDED',ports='NONE',evidence=str(LAB/'logs/network-exceptions.jsonl'))
add_smoke(smoke_id='presidio-02',candidate_id='presidio',stage='corrected_fixture',status='PASS',source_inspected='true',install_attempted='true',service_or_cli_started='false',library_fixture_executed='true',fixture_passed='true',integration_fit_proven='false',command='sandbox-exec -p (version 1)(allow default)(deny network*) envs/presidio/.venv/bin/python fixtures/presidio_fixture.py',expected='one EMAIL_ADDRESS result and redacted output',real_output='PASS presidio_custom_recognizer matches=1 redacted=Contact <EMAIL_ADDRESS> with receipt.invalid only.',duration_seconds=last_duration('presidio','presidio_fixture.py'),network_runtime='DENIED_BY_SANDBOX_AND_PASS',ports='NONE',evidence=str(LAB/'logs/presidio.log'))
for key,reason in notrun_reason.items():
    add_smoke(smoke_id=f'{key}-00',candidate_id=key,stage='source_only',status='NOT_RUN',source_inspected='true',install_attempted='false',service_or_cli_started='false',library_fixture_executed='false',fixture_passed='false',integration_fit_proven='false',command='NOT_RUN',expected='NOT_RUN',real_output=reason,duration_seconds='',network_runtime='NOT_APPLICABLE',ports='NONE',evidence=str(LAB/f'inspected/{key}'))
write_csv('deployment-smoke-results.csv',list(smokes[0]),smokes)

resources=[]
fixture_needles={'langgraph':'langgraph_fixture.py','opa':'opa test','opentelemetry':'opentelemetry_fixture.py','promptfoo':'result.json','presidio':'presidio_fixture.py'}
for key,s in specs.items():
    m=meta[key]
    resources.append({'candidate_id':key,'candidate':s['label'],'install_attempted':str(key in smoked).lower(),'source_checkout_bytes':m['source_checkout_bytes'],'inspected_evidence_bytes':m['inspected_bytes'],'environment_bytes':m['environment_bytes'],'install_or_download_duration_seconds':m['install_network_duration_seconds'] or 'NOT_RUN','fixture_duration_seconds':last_duration(key,fixture_needles[key]) if key in smoked else 'NOT_RUN','peak_fixture_rss_bytes':m['peak_fixture_rss_bytes'] or 'NOT_RUN','idle_cpu':'NOT_APPLICABLE_NO_PERSISTENT_SERVICE','idle_ram_bytes':'NOT_APPLICABLE_NO_PERSISTENT_SERVICE','bound_ports':'NONE','loopback_only':'true','runtime_egress':'PASS_UNDER_NETWORK_DENY' if key in smoked else 'NOT_RUN','install_egress':('UNPLANNED_SPACY_MODEL_400.7MB_PLUS_PYPI' if key=='presidio' else ('PUBLIC_PACKAGE_OR_RELEASE_FETCHES_LOGGED' if key in smoked else 'SOURCE_INSPECTION_FETCHES_ONLY')),'download_size_gate':'PASS_TOTAL_LAB_3.106GB_LT_10GB; NO_SINGLE_ARTIFACT_GT_2GB','cleanup_state':'RETAINED_DISPOSABLE_FOR_AUDIT','evidence':str(LAB/'lab-summary.json')})
write_csv('resource-profile.csv',list(resources[0]),resources)

contracts=[]
for key,s in specs.items():
    contracts.append({'candidate_id':key,'candidate':s['label'],'authority_role':s['authority'],'pause_resume_semantics':s['pause'],'idempotency_semantics':s['idem'],'data_model':s['data'],'local_operations':s['ops'],'replaceability':s['replace'],'helixar_contract_mapping':s['mapping'],'integration_fit_proven':'false','bounded_lab_fit':s['fit'],'production_suitability':'UNKNOWN','unresolved_conflict_or_decision':s['unresolved']})
write_csv('contract-fit.csv',list(contracts[0]),contracts)

cleanup=[]
for key,s in specs.items():
    paths=[str(LAB/f'inspected/{key}')]
    if meta[key]['source_checkout_bytes']: paths.append(str(LAB/f'sources/{key}'))
    if meta[key]['environment_bytes']: paths.append(str(LAB/f'envs/{key}'))
    cleanup.append({'candidate_id':key,'candidate':s['label'],'lab_paths':';'.join(paths),'process_state':'EXITED_NO_SERVICE_RETAINED','bound_ports':'NONE','cleanup_command':f"rm -rf '{LAB}/envs/{key}' '{LAB}/sources/{key}' '{LAB}/inspected/{key}'",'cleanup_executed':'false','cleanup_verified':'NOT_RUN_RETAINED_FOR_EVIDENCE','retention_reason':'Disposable evidence retained for human review; no daemon/listener remains.','external_state_created':'NONE','external_cleanup_required':'false'})
cleanup.append({'candidate_id':'lab','candidate':'O01 lab root','lab_paths':str(LAB),'process_state':'NO_TRACKED_BACKGROUND_PROCESS','bound_ports':'NONE','cleanup_command':f"rm -rf '{LAB}'",'cleanup_executed':'false','cleanup_verified':'NOT_RUN_RETAINED_FOR_EVIDENCE','retention_reason':'Run logs, fixtures, exact source snapshots and smoke artifacts retained until review.','external_state_created':'NONE','external_cleanup_required':'false'})
write_csv('cleanup-manifest.csv',list(cleanup[0]),cleanup)

mandatory=[
 'AGENTS.md','000_HOME.md','05_Data/Current State/Dystopia Current Snapshot.md','04_Logs/Daily/Daily Log - 2026-07-14.md',
 '02_Projects/Helixar World-Class Benchmark Program/00 Helixar World-Class Benchmark Program - Control Center.md',
 '02_Projects/Helixar World-Class Benchmark Program/02 Current Architecture Benchmark.md',
 '02_Projects/Helixar World-Class Benchmark Program/04 Cross-Packet Implementation Readiness Audit - 2026-07-14.md',
 '02_Projects/Helixar World-Class Benchmark Program/05 Hermes Parallel Architecture and Build Roadmap.md',
 '02_Projects/Helixar World-Class Benchmark Program/06 Folder and Evidence Use Guide.md',
 '02_Projects/Helixar World-Class Benchmark Program/Hermes Launch Prompts/Wave A/O01 Control Plane Trust and Observability OSS Lab.md',
 '02_Projects/Helixar World-Class Benchmark Program/Packets/R01 Sol-Fleet Research and Architecture Packet.md',
 '02_Projects/Helixar World-Class Benchmark Program/Packets/R02 Sol-Trust Research and Architecture Packet.md']
for lane in ['R01 Sol-Fleet','R02 Sol-Trust','R03 Terra-Authority','R04 Terra-Market','R05 Terra-Pain','R06 Luna-Creative','R07 Mars-GTM','R08 Mars-Measurement','R09 Mars-Economics','R10 Mercury-Talent']:
    mandatory.extend([f'05_Data/Helixar World-Class Benchmark Program/{lane}/open-source-inventory.csv',f'05_Data/Helixar World-Class Benchmark Program/{lane}/evidence-ledger.csv'])

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
read_lines='\n'.join(f"- `{DYS/x}` — SHA-256 `{sha256(DYS/x)}`" for x in mandatory)
repo_lines='\n'.join(f"- **{specs[k]['label']}** — `{meta[k]['repository']}` @ `{('e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297' if k=='opa' else meta[k]['commit'])}`; inspected `{'; '.join(meta[k]['inspected_paths'])}`" for k in specs)
summary_rows='\n'.join(f"| {s['label']} | {s['category']} | {s['classification']} | {'PASS' if k in smoked else 'NOT_RUN'} | {s['fit']} |" for k,s in specs.items())
report=f'''---
title: O01 Control Plane, Trust and Observability OSS Lab Report
date: 2026-07-14
status: complete-lab-evidence-production-unknown
scope: R01 Sol-Fleet; R02 Sol-Trust
lab_root: {LAB}
---

# O01 Control Plane, Trust and Observability OSS Lab Report

## Executive verdict

**Do not select a monolithic control platform.** Keep Helixar authority in its own append-only authority ledger and typed contracts. Use replaceable components beneath that boundary.

1. **ADOPT OpenTelemetry as the transport/interface, not as authority.** The Python SDK emitted one in-memory span with three allowlisted Helixar attributes and zero prompt/completion/tool-argument attributes; the same fixture passed with all network access denied.
2. **ADAPT LangGraph only as an in-process specialist runtime.** Its checkpointed interrupt/resume fixture proved zero pre-resume effects and exactly one synthetic post-resume effect. It did not prove durable database recovery, cross-process replay, or integration with a Helixar repository.
3. **OPA is the strongest technically exercised policy candidate, but remains `POC_MORE`, not a silent architecture choice.** OPA v1.18.2 passed three same-tenant/hash-bound tests and direct allow/deny queries. The required human H0 OPA-versus-Cedar decision remains open; Cedar was source-inspected but not installed because Rust was absent.
4. **ADAPT Promptfoo as a replaceable evaluation runner.** One deterministic echo case and two assertions passed with zero model tokens under a network-deny sandbox. `npm audit --omit=dev` reported zero known vulnerabilities at install time, but the installation contained 825 production/optional/peer dependency entries and consumed 1.559 GB.
5. **ADAPT Presidio only as defense in depth.** The final custom `.invalid` email redaction fixture passed under network denial, but initial construction unexpectedly downloaded a 400.7 MB spaCy model and the successful fixture peaked at 690.6 MB RSS. Presidio itself warns that automated detection cannot guarantee complete sensitive-data discovery.
6. **Do not adopt Phoenix code in this OSS lane.** The selected commit carries Elastic License 2.0. Langfuse core is MIT but has a separate `ee/LICENSE`; any later use must keep that boundary explicit.
7. **Temporal remains the durability benchmark, not the P0 default.** Trigger.dev and Prefect are execution/scheduling candidates, not control-plane authority. OpenFGA is relationship authorization and is rejected for P0 policy fit.

Five final deterministic fixtures passed: one orchestrator/library, one policy CLI, and three evaluation/observability/security libraries or CLIs. No service was started, no port was bound, all final fixtures passed under macOS `sandbox-exec` with `deny network*`, no implementation repository was edited, and no external system was mutated. **Integration fit and production suitability remain unproven for every candidate.**

## Scope and non-claims

- Wave A only: source audit, architecture comparison and disposable localhost/offline lab.
- Dystopia was used only as evidence/decision memory and derivative report storage, never as runtime state.
- No credentials, customer data, Ultron excluded sources, hosted APIs, live connectors, CRM/ATS/finance systems or business actions were accessed.
- Synthetic values used only `.invalid` domains.
- A source checkout is not called a deployment proof. Only the five listed fixtures receive `PASS`.
- `source_inspected`, `install_attempted`, `service_or_cli_started`, `library_fixture_executed`, `deterministic_fixture_passed`, `integration_fit_proven` and `production_suitability_unknown` are separate columns in the CSV evidence.
- No daemon was necessary for the bounded fixtures; therefore idle daemon CPU/RAM is `NOT_APPLICABLE_NO_PERSISTENT_SERVICE`, not zero.

## Candidate disposition

| Candidate | Surface | Classification | Final fixture | Bounded fit |
|---|---|---:|---:|---:|
{summary_rows}

## Control-plane comparison

### Authority

Temporal, LangGraph, Trigger.dev and Prefect may execute work but must not own approval truth, tenant authority, canonical receipts or final state transitions. OPA/Cedar may compute policy decisions but enforcement and receipt validity remain Helixar-owned. OpenTelemetry/OpenInference and every eval/observability product are evidence surfaces only.

### Pause/resume and durability

- **Temporal:** strongest server-backed replay/history benchmark; not run due absent Go/Docker and because P0 architecture currently favors the simpler authority ledger.
- **LangGraph:** bounded interrupt/resume proven with `MemorySaver`; this proves graph semantics, not crash durability.
- **Trigger.dev / Prefect:** source surfaces support waits/stateful orchestration patterns, but local self-host recovery was not run.
- Policy, telemetry, redaction and eval candidates do not provide control-plane pause/resume semantics.

### Idempotency

No candidate eliminates business-side-effect idempotency. Helixar still requires a canonical key bound to tenant, proposal/action, target hash, policy version and approval scope. Temporal adds deterministic replay and run/activity IDs; LangGraph adds thread/checkpoint continuity; OPA/Cedar are deterministic for fixed inputs; telemetry may duplicate; eval results require pinned configs/datasets/source hashes.

### Data model and replaceability

The machine-readable comparison is in `contract-fit.csv`. The replacement rule is: normalize each component behind Helixar-owned ports and persist canonical authority/evidence outside vendor-specific stores. OpenTelemetry and simple CLI artifact formats are highest-replaceability. Temporal workflow history and self-hosted observability application schemas have the highest migration coupling.

## Real smoke evidence

### LangGraph — PASS

- Selected source: `{meta['langgraph']['repository']}` @ `{meta['langgraph']['commit']}`.
- Installed local editable packages in an isolated Python 3.13 venv.
- Fixture: graph interrupts before execution; checkpoint has `next == ('approval_gate',)`; resume with `Command(resume=True)` produces value `2` and one synthetic effect.
- Real output: `PASS langgraph_interrupt_resume value=2 effects=1 pre_resume_effects=0`.
- Runtime: 3.15 s, 80,707,584-byte peak RSS; network-deny rerun passed; no ports.

### OPA — PASS

- Downloaded v1.18.2 static Darwin arm64 binary; release SHA-256 file verified; build commit `{ 'e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297' }` matched fetched tag commit.
- Rego policy allows only same-tenant `propose` when approval target hash equals resource target hash.
- Real output: three tests `PASS`; direct allow query `true`; cross-tenant query `false`.
- Runtime: 0.06 s, 30,343,168-byte peak RSS; network-deny rerun passed; CLI only, no port.

### OpenTelemetry — PASS

- SDK 1.43.0 in isolated venv; selected spec source commit `{meta['opentelemetry']['commit']}`.
- One in-memory span emitted with tenant, policy version and receipt ID; content attributes excluded.
- Real output: `PASS otel_in_memory_export spans=1 sensitive_content_attributes=0`.
- Runtime: 0.06 s, 24,297,472-byte peak RSS; network-deny rerun passed; no exporter egress and no port.

### Promptfoo — PASS

- Version 0.121.19; telemetry and remote generation disabled; cache disabled.
- Echo fixture used only `.invalid` values; exact-output and prohibited-domain assertions both passed.
- Real output: `1 passed (100%); 0 failed; 0 errors`; JSON artifact records score 1, two passing assertions and zero tokens.
- Runtime: 2.92 s, 238,338,048-byte peak RSS; network-deny rerun passed; no port.
- Security: `npm audit --omit=dev --json` reported zero known vulnerabilities across all severities at run time; this is time-bounded registry evidence, not a production security review.

### Presidio — FAIL then PASS

- Analyzer/anonymizer 2.2.363 installed from selected source commit `{meta['presidio']['commit']}`.
- Initial run unexpectedly downloaded `en_core_web_lg-3.8.0` (400.7 MB) even though the fixture passed `nlp_engine=None`; this was detected in process output and retroactively logged in `network-exceptions.jsonl`.
- A regex escaping defect then produced no match; after correction, exactly one email match was anonymized.
- Final real output: `PASS presidio_custom_recognizer matches=1 redacted=Contact <EMAIL_ADDRESS> with receipt.invalid only.`
- Final runtime: 1.81 s, 690,601,984-byte peak RSS; network-deny rerun passed; no port.

## Operations, resources and egress

- Current retained lab size: **3,105,782,968 bytes (3.106 GB)**, below the 10 GB lane limit. No single fetched artifact exceeded 2 GB.
- No service was exposed. All fixtures were CLI/library processes and bound **no ports**; final runs succeeded while all network access was denied.
- Network audit at the pre-deliverable summary point recorded 134 explicit network commands plus one unplanned Presidio model fetch. Final counters are frozen in the dated run receipt after validation.
- External writes/business mutations: **0**. Public Git/source/package/release operations were reads/downloads only.
- Promptfoo had the largest environment (1,558,744,644 bytes); Presidio had the largest successful fixture RSS (690,601,984 bytes).
- The lab is intentionally retained as disposable evidence. `cleanup-manifest.csv` gives exact removal commands; no daemon or external state requires cleanup.

## License and security gates

All exact root license files were hashed at the selected commits. Permissive licenses do not imply production approval. Phoenix is blocked in this OSS lane by Elastic-2.0. Langfuse has an MIT root plus a separate enterprise license boundary. Dependency CVE scans were not run for Python candidates; `pip check` only proved dependency consistency after removing the host `PYTHONPATH` from the checks. Production security suitability is `UNKNOWN` for every candidate.

## Conflicts and required human decisions

1. **H0 policy engine:** choose OPA or Cedar. OPA has bounded technical proof; Cedar has source/license proof only. OpenFGA does not substitute for either.
2. **Durability escalation:** decide the measurable threshold that justifies Temporal or another server-backed orchestrator instead of the P0 authority ledger plus Hermes scheduling.
3. **Observability viewer:** decide whether any self-hosted viewer is needed before canonical event/receipt contracts are stable. Phoenix requires legal approval; Langfuse needs explicit core/EE boundaries.
4. **Trace privacy:** approve the exact OpenTelemetry/OpenInference attribute allowlist, redaction order, retention and sampling policy.
5. **Presidio packaging:** approve or reject a fixed, pre-provisioned NLP model strategy; prohibit runtime model auto-downloads in production.
6. **Evaluation split:** decide whether Promptfoo alone covers initial gates or whether Inspect AI receives a second code-native POC.
7. **Strategic architecture tracks:** this lab does not reconcile autonomous demand authority infrastructure with the human-response video-intelligence draft track; all recommendations are infrastructure-level and compatible only after that product decision is recorded.

## Acceptance matrix

| Gate | Status | Evidence |
|---|---|---|
| Every assigned candidate accounted for | PASS | 17 rows in `candidate-inventory.csv`; 17 contract rows; deployment rows include all 17 candidates. |
| Primary repositories and relevance | PASS | Exact repository and commit per inventory row and repository appendix below. |
| At least one orchestrator smoke | PASS | LangGraph interrupt/resume fixture. |
| At least one policy smoke | PASS | OPA v1.18.2 three tests plus allow/deny queries. |
| At least two eval/observability smokes | PASS | OpenTelemetry, Promptfoo and Presidio final fixtures. |
| Every PASS has real command/output evidence | PASS | `deployment-smoke-results.csv` plus per-candidate logs under `{LAB}/logs`. |
| Exact license and commit recorded | PASS | `license-and-security.csv`; license SHA-256 values; OPA tag/commit corrected. |
| No code adoption where license unresolved | PASS | No unresolved exact license; Phoenix classified `REJECT_LICENSE`; no code copied. |
| Loopback-only/no exposed service | PASS | No service started, no bound ports; final fixtures passed under network denial. |
| No implementation repository/runtime mutation | PASS | Only disposable lab and required Dystopia evidence files written. |
| Production suitability proven | NOT_CLAIMED | Explicitly `UNKNOWN` for all candidates. |

## Exact Dystopia files read

{read_lines}

## Exact repositories and source files inspected

{repo_lines}

## Evidence map

- Candidate accounting: `{OUT/'candidate-inventory.csv'}`
- License/security: `{OUT/'license-and-security.csv'}`
- Smoke commands and outputs: `{OUT/'deployment-smoke-results.csv'}`
- Resource/egress: `{OUT/'resource-profile.csv'}`
- Contract comparison: `{OUT/'contract-fit.csv'}`
- Cleanup: `{OUT/'cleanup-manifest.csv'}`
- Raw auditable process/network log: `{LAB/'logs/process-network.jsonl'}`
- Unplanned egress exception: `{LAB/'logs/network-exceptions.jsonl'}`
- Exact source metadata: `{LAB/'source-metadata.json'}`
- Lab summary: `{LAB/'lab-summary.json'}`
'''
REPORT.write_text(report,encoding='utf-8')
print(json.dumps({'report':str(REPORT),'csvs':[str(p) for p in sorted(OUT.glob('*.csv'))],'candidate_count':len(inv),'smoke_rows':len(smokes)},indent=2))
