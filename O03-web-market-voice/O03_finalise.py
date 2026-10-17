#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LAB = Path('/Users/vedantswami/Projects/helixar-oss-labs/O03-web-market-voice')
DYS = Path('/Users/vedantswami/Projects/Dystopia/Dystopia')
ARCH = DYS / '02_Projects/Helixar World-Class Benchmark Program/Architecture/10 O03 Web Market and Voice OSS Adoption Report.md'
OUT = DYS / '05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice'
RECEIPT = DYS / '04_Logs/Runs/2026-07-14 - O03 Web Market and Voice OSS Lab Run Receipt.md'
OUT.mkdir(parents=True, exist_ok=True)
ARCH.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)

meta = {x['name']: x for x in json.loads((LAB / 'source-metadata.json').read_text())}
proc = [json.loads(x) for x in (LAB / 'process-log.jsonl').read_text().splitlines() if x.strip()]
net = [json.loads(x) for x in (LAB / 'network-log.jsonl').read_text().splitlines() if x.strip()]
services = [json.loads(x) for x in (LAB / 'service-log.jsonl').read_text().splitlines() if x.strip()]

names = ['lighthouse','crawlee','unlighthouse','siteone','changedetection','readability','openrefine','splink','dedupe','taguette','doccano','argilla','formbricks','whisper','bertopic']
display = {
'lighthouse':'Lighthouse','crawlee':'Crawlee','unlighthouse':'Unlighthouse','siteone':'SiteOne Crawler',
'changedetection':'changedetection.io','readability':'Mozilla Readability','openrefine':'OpenRefine','splink':'Splink',
'dedupe':'dedupe','taguette':'Taguette','doccano':'doccano','argilla':'Argilla','formbricks':'Formbricks',
'whisper':'OpenAI Whisper','bertopic':'BERTopic'}
category = {
'lighthouse':'web audit','crawlee':'crawl orchestration','unlighthouse':'site-wide audit orchestration','siteone':'site crawler',
'changedetection':'web capture/diff','readability':'HTML extraction','openrefine':'analyst reconciliation','splink':'entity resolution',
'dedupe':'entity resolution','taguette':'qualitative coding','doccano':'text annotation','argilla':'human-feedback curation',
'formbricks':'survey delivery','whisper':'speech transcription','bertopic':'topic suggestion'}
lane = {n:'R03' for n in ['lighthouse','crawlee','unlighthouse','siteone']}
lane.update({n:'R04' for n in ['changedetection','readability','openrefine','splink','dedupe']})
lane.update({n:'R05' for n in ['taguette','doccano','argilla','formbricks','whisper','bertopic']})
license_spdx = {
'lighthouse':'Apache-2.0 core; bundled third-party MPL-2.0/BSD/MIT notices','crawlee':'Apache-2.0','unlighthouse':'MIT','siteone':'MIT',
'changedetection':'Apache-2.0 repository core','readability':'Apache-2.0','openrefine':'BSD-3-Clause','splink':'MIT','dedupe':'MIT',
'taguette':'BSD-3-Clause; installer notice also references GPL-3.0 Calibre','doccano':'MIT','argilla':'Apache-2.0','formbricks':'AGPL-3.0 core plus separate enterprise licensing','whisper':'MIT','bertopic':'MIT'}
classification = {
'lighthouse':'ADOPT','crawlee':'POC_MORE','unlighthouse':'POC_MORE','siteone':'POC_MORE','changedetection':'POC_MORE',
'readability':'ADAPT','openrefine':'POC_MORE','splink':'ADAPT','dedupe':'POC_MORE','taguette':'POC_MORE','doccano':'POC_MORE',
'argilla':'POC_MORE','formbricks':'PARTNER','whisper':'ADAPT','bertopic':'POC_MORE'}
installed = {n: n in {'lighthouse','readability','splink','whisper'} for n in names}
started = {n: n == 'lighthouse' for n in names}
fixture = installed.copy()
passed = installed.copy()
versions = {
'lighthouse':'13.4.0; source commit '+meta['lighthouse']['commit'],
'readability':'0.6.0; source commit '+meta['readability']['commit'],
'splink':'5.0.0.dev4; source commit '+meta['splink']['commit'],
'whisper':'20250625; source commit '+meta['whisper']['commit']}
relevance = {
'lighthouse':'Deterministic local page-quality evidence for Oracle/OA2 behind a rights-aware source registry.',
'crawlee':'Read-only crawl orchestration candidate with queues, limits and provenance hooks.',
'unlighthouse':'Site-wide Lighthouse orchestration candidate; requires comparison against simpler adapters.',
'siteone':'Compiled site crawler and export candidate; runtime and schema not exercised.',
'changedetection':'Capture/diff primitive for append-only market observations, not truth or alert authority.',
'readability':'Deterministic article-text extraction after source-rights gate with raw-snapshot hash retained.',
'openrefine':'Offline analyst QA/reconciliation workbench; never runtime source of truth.',
'splink':'Probabilistic candidate-pair generator beneath reversible AliasDecision review.',
'dedupe':'Human-trained alternative candidate generator; precision and drift need labeled evaluation.',
'taguette':'Quote highlight/tag UX and export reference; not the Moriarty backend.',
'doccano':'Assignment, labeling, review and adjudication pattern mapped to Moriarty contracts.',
'argilla':'Human-feedback queue and evaluation reference with maintenance-roadmap risk.',
'formbricks':'Survey delivery partner/service boundary only pending mixed-license and data-governance review.',
'whisper':'Replaceable local ASR adapter producing timecoded machine candidates for human review.',
'bertopic':'Candidate theme/drift suggestion adapter; never activates PainCodes autonomously.'}
next_gate = {
'lighthouse':'Add rights/robots/terms registry gate and normalized AuditObservation adapter; production browser sandbox and patch cadence remain unproven.',
'crawlee':'Run the same localhost corpus against Crawlee and SiteOne; compare robots, rate-limit, provenance and export schemas.',
'unlighthouse':'Only test if site-wide orchestration remains needed after Lighthouse adapter proof.',
'siteone':'Run exact local corpus and compare output determinism/resource use with Crawlee.',
'changedetection':'Run deterministic two-snapshot diff fixture with sanitization and append-only SourceSnapshot mapping.',
'readability':'Wrap behind extractor port; add hostile-HTML/sanitization and copyright-retention fixtures.',
'openrefine':'Define receipted import/export transform protocol before any analyst pilot.',
'splink':'Build labeled entity-resolution benchmark with precision/recall thresholds; keep all merges human/reversible.',
'dedupe':'Benchmark against Splink only if labeled active-learning workflow justifies second engine.',
'taguette':'Map export fields to QuoteSpan/ReviewDecision on synthetic data; retain canonical storage in Moriarty.',
'doccano':'Prototype read/write adapter against synthetic assignments and adjudication receipts.',
'argilla':'No embed decision until maintenance status, export fidelity and security are reviewed.',
'formbricks':'Legal/security/procurement review; API/service isolation only; no code copying authorized.',
'whisper':'Benchmark language/noise bias, diarization gap, deletion propagation and consent/retention workflow.',
'bertopic':'Run seeded stability/drift benchmark; human taxonomy activation and replay receipts mandatory.'}

# Measured sizes.
def tree_bytes(p: Path) -> int:
    total = 0
    if p.exists():
        for q in p.rglob('*'):
            if q.is_file() and not q.is_symlink():
                try: total += q.stat().st_size
                except OSError: pass
    return total
repo_bytes = {n: tree_bytes(LAB/'repos'/n) for n in names}
env_bytes = {n: tree_bytes(LAB/'candidates'/n) for n in names}
lab_bytes = tree_bytes(LAB)
large_files = []
for p in LAB.rglob('*'):
    if p.is_file() and not p.is_symlink():
        try:
            if p.stat().st_size > 2_000_000_000: large_files.append(str(p))
        except OSError: pass

# Final proven runtime measurements from /usr/bin/time -l.
fixture_duration = {'lighthouse':10.709,'readability':0.379,'splink':0.558,'whisper':4.186}
peak_rss = {'lighthouse':268009472,'readability':98713600,'splink':117325824,'whisper':698548224}
install_ids = {
'lighthouse':['install-lighthouse','install-lighthouse-retry','install-lighthouse-dev-retry','build-lighthouse-report'],
'readability':['install-readability'],'splink':['create-venv-splink','install-splink','install-splink-pyarrow'],
'whisper':['create-venv-whisper','install-whisper','download-whisper-tiny-en']}
install_duration = {n: round(sum(float(r['duration_seconds']) for r in proc if r['process_id'] in install_ids.get(n,[])),3) for n in names}

# Candidate inventory.
inv_fields = ['candidate_id','candidate','category','source_lane_ids','repository_url','selected_ref','selected_commit','source_hash_type','source_hash','source_inspected','inspected_files','install_attempted','service_or_cli_started','library_fixture_executed','deterministic_fixture_passed','integration_fit_proven','production_suitability_unknown','classification','selected_component_version','relevance','notes']
inv_rows=[]
for n in names:
    m=meta[n]
    inspected=';'.join(x['path'] for x in m['license_files'])+';'+';'.join(m.get('manifests',[])[:5])
    inv_rows.append({
        'candidate_id':n,'candidate':display[n],'category':category[n],'source_lane_ids':lane[n],
        'repository_url':m['repository'].removesuffix('.git'),'selected_ref':m.get('head_tag') or 'origin/default-head',
        'selected_commit':m['commit'],'source_hash_type':'git_commit_sha1 plus git_archive_sha256','source_hash':m['archive_sha256'],
        'source_inspected':'true','inspected_files':inspected,'install_attempted':str(installed[n]).lower(),
        'service_or_cli_started':str(started[n]).lower(),'library_fixture_executed':str(fixture[n]).lower(),
        'deterministic_fixture_passed':str(passed[n]).lower(),'integration_fit_proven':'false',
        'production_suitability_unknown':'true','classification':classification[n],
        'selected_component_version':versions.get(n,'source snapshot at '+m['commit']),
        'relevance':relevance[n],'notes':next_gate[n]})

# License/security.
lic_fields=['candidate_id','candidate','repository_url','selected_commit','license_path','spdx_or_exact_license','license_sha256','code_adoption_allowed','secondary_license_boundary','dependency_security_check','vulnerability_result','security_observation','production_security_suitability','license_classification']
lic_rows=[]
for n in names:
    m=meta[n]; root=m['license_files'][0]
    dep='NOT_RUN_CVE_SCAN'; vuln='UNKNOWN'
    if n=='lighthouse': dep='PASS npm audit --offline --omit=dev'; vuln='0 info/low/moderate/high/critical; 1309 dependency entries including dev/optional'
    elif n=='readability': dep='PASS npm audit --offline'; vuln='0 info/low/moderate/high/critical; 69 dependency entries'
    elif n in ('splink','whisper'): dep='PASS isolated pip check; NOT_RUN_CVE_SCAN'; vuln='UNKNOWN'
    allowed='true'
    boundary='NONE_OBSERVED_AT_ROOT; transitive/component review still required'
    if n=='formbricks':
        allowed='false_pending_legal'; boundary='AGPL-3.0 core plus separate enterprise feature/license boundary; use service/API only pending review'
    elif n=='lighthouse': boundary='Bundled third-party licenses recorded; adapter distribution needs notice inventory'
    elif n=='taguette': boundary='scripts/dist installer includes separately licensed Calibre; do not redistribute installer without review'
    lic_rows.append({'candidate_id':n,'candidate':display[n],'repository_url':m['repository'].removesuffix('.git'),
      'selected_commit':m['commit'],'license_path':root['path'],'spdx_or_exact_license':license_spdx[n],
      'license_sha256':root['sha256'],'code_adoption_allowed':allowed,'secondary_license_boundary':boundary,
      'dependency_security_check':dep,'vulnerability_result':vuln,
      'security_observation':'Exact source/license snapshot inspected; localhost/synthetic-only smoke where run; no production security assessment.',
      'production_security_suitability':'UNKNOWN','license_classification':classification[n]})

# Smoke results: exactly one terminal row per candidate, with four real passes.
smoke_fields=['smoke_id','candidate_id','stage','status','source_inspected','install_attempted','service_or_cli_started','library_fixture_executed','fixture_passed','integration_fit_proven','command','expected','real_output','duration_seconds','network_runtime','ports','evidence']
smoke_rows=[]
pass_rows={
'lighthouse':('O03-lighthouse-loopback-isolated-final','loopback_page_audit','/usr/bin/env -u PYTHONPATH ... python3 lighthouse_smoke.py','localhost page audit has accessibility/best-practices/SEO categories','PASS accessibility=1 best-practices=0.96 seo=1; requested and final URLs loopback','LOOPBACK_ONLY','127.0.0.1:18731',LAB/'artifacts/lighthouse/summary.json'),
'readability':('O03-readability-offline-final','deterministic_extraction','sandbox-exec ... node candidates/readability/smoke.mjs','repeat-equal article extraction with expected synthetic sentence','PASS exact repeat; title/text assertions pass; output hash cbd8233c...','DENIED_BY_SANDBOX_AND_PASS','NONE',LAB/'artifacts/readability/summary.json'),
'splink':('O03-splink-offline-isolated-final','deterministic_candidate_linkage','sandbox-exec ... candidates/splink/venv/bin/python candidates/splink/smoke.py','one blocked candidate pair; repeat-equal; no merge/write','PASS pair r1-r2 probability=0.6735395189; input unchanged','DENIED_BY_SANDBOX_AND_PASS','NONE',LAB/'artifacts/splink/summary.json'),
'whisper':('O03-whisper-offline-isolated-final','deterministic_local_transcription','sandbox-exec ... candidates/whisper/venv/bin/python candidates/whisper/smoke.py','repeat-equal local ASR with segment and word timecodes','PASS exact transcript repeat; fixture/model hashes and timecodes recorded','DENIED_BY_SANDBOX_AND_PASS','NONE',LAB/'artifacts/whisper/summary.json')}
for n in names:
    if n in pass_rows:
        sid,stage,cmd,exp,real,nw,ports,evidence=pass_rows[n]
        smoke_rows.append({'smoke_id':sid,'candidate_id':n,'stage':stage,'status':'PASS','source_inspected':'true','install_attempted':'true','service_or_cli_started':str(started[n]).lower(),'library_fixture_executed':'true','fixture_passed':'true','integration_fit_proven':'false','command':cmd,'expected':exp,'real_output':real,'duration_seconds':fixture_duration[n],'network_runtime':nw,'ports':ports,'evidence':str(evidence)})
    else:
        smoke_rows.append({'smoke_id':n+'-source-only','candidate_id':n,'stage':'source_only','status':'NOT_RUN','source_inspected':'true','install_attempted':'false','service_or_cli_started':'false','library_fixture_executed':'false','fixture_passed':'false','integration_fit_proven':'false','command':'NOT_RUN','expected':'NOT_RUN','real_output':next_gate[n],'duration_seconds':'','network_runtime':'NOT_APPLICABLE','ports':'NONE','evidence':str(LAB/'repos'/n)})

# Resource profile.
res_fields=['candidate_id','candidate','install_attempted','source_checkout_bytes','environment_bytes','install_or_download_duration_seconds','fixture_duration_seconds','peak_fixture_rss_bytes','idle_cpu','idle_ram_bytes','bound_ports','loopback_only','runtime_egress','install_egress','download_size_gate','cleanup_state','evidence']
res_rows=[]
for n in names:
    res_rows.append({'candidate_id':n,'candidate':display[n],'install_attempted':str(installed[n]).lower(),
      'source_checkout_bytes':repo_bytes[n],'environment_bytes':env_bytes[n],
      'install_or_download_duration_seconds':install_duration[n] if installed[n] else 'NOT_RUN',
      'fixture_duration_seconds':fixture_duration.get(n,'NOT_RUN'),'peak_fixture_rss_bytes':peak_rss.get(n,'NOT_RUN'),
      'idle_cpu':'NOT_APPLICABLE_NO_PERSISTENT_SERVICE','idle_ram_bytes':'NOT_APPLICABLE_NO_PERSISTENT_SERVICE',
      'bound_ports':'127.0.0.1:18731 TRANSIENT' if n=='lighthouse' else 'NONE','loopback_only':'true',
      'runtime_egress':'LOOPBACK_ONLY' if n=='lighthouse' else ('PASS_UNDER_NETWORK_DENY' if n in pass_rows else 'NOT_RUN'),
      'install_egress':'PUBLIC_GIT_OR_PACKAGE_FETCHES_LOGGED' if installed[n] else 'SOURCE_CLONE_ONLY',
      'download_size_gate':f'PASS_TOTAL_LAB_{lab_bytes}_BYTES_LT_10GB; NO_SINGLE_FILE_GT_2GB',
      'cleanup_state':'RETAINED_DISPOSABLE_FOR_AUDIT_NO_SERVICE','evidence':str(LAB/'process-log.jsonl')})

# Contract fit.
contract_fields=['candidate_id','candidate','authority_boundary','source_rights_or_consent_boundary','provenance_boundary','deterministic_vs_probabilistic','local_operations','replaceability','helixar_contract_mapping','integration_fit_proven','bounded_lab_fit','production_suitability','unresolved_conflict_or_decision']
contract_rows=[]
for n in names:
    if lane[n]=='R03':
        rights='Collector disabled unless versioned rights/terms/robots record permits; robots is required but not legal authorization.'
        prov='PageSnapshot/source observation keeps fetched_at, content hash, HTTP/canonical/robots state and artifact pointer.'
    elif lane[n]=='R04':
        rights='Rights record must be approved and unexpired before ingestion; preserve snapshot hash and permitted transformation.'
        prov='Append-only SourceSnapshot/Claim/AliasDecision lineage; no silent identity merge or overwrite.'
    else:
        rights='Study/source purpose, consent, retention and withdrawal/deletion state precede processing; public evidence must still be ethical/permitted.'
        prov='EvidenceArtifact hash resolves to exact QuoteSpan offsets/timecodes, model/transformation lineage and review state.'
    det = 'Deterministic adapter/output checks; probabilistic outputs remain candidates requiring review.'
    if n in ('splink','dedupe','whisper','bertopic'): det='Probabilistic candidate generation only; pinned source/model/config plus deterministic lineage, thresholds and human review.'
    contract_rows.append({'candidate_id':n,'candidate':display[n],
      'authority_boundary':'Component is replaceable and subordinate; Helixar owns permissions, canonical evidence, decisions, receipts and external writes.',
      'source_rights_or_consent_boundary':rights,'provenance_boundary':prov,'deterministic_vs_probabilistic':det,
      'local_operations':'Library/CLI or source snapshot in disposable O03 lab; no production deployment or credentials.',
      'replaceability':'HIGH behind a narrow adapter/service port' if n!='formbricks' else 'HIGH through isolated API/service boundary; no code adoption',
      'helixar_contract_mapping':relevance[n],'integration_fit_proven':'false','bounded_lab_fit':classification[n],
      'production_suitability':'UNKNOWN','unresolved_conflict_or_decision':next_gate[n]})

# Cleanup manifest.
cleanup_fields=['candidate_id','candidate','lab_paths','process_state','bound_ports','cleanup_command','cleanup_executed','cleanup_verified','retention_reason','external_state_created','external_cleanup_required']
cleanup_rows=[]
for n in names:
    paths=[LAB/'repos'/n]
    if (LAB/'candidates'/n).exists(): paths.append(LAB/'candidates'/n)
    cleanup_rows.append({'candidate_id':n,'candidate':display[n],'lab_paths':';'.join(map(str,paths)),
      'process_state':'EXITED_NO_SERVICE_RETAINED','bound_ports':'NONE',
      'cleanup_command':'rm -rf '+' '.join(repr(str(p)) for p in paths),'cleanup_executed':'false',
      'cleanup_verified':'NO_DAEMON_OR_LISTENER_REMAINS; evidence retained','retention_reason':'Disposable exact source, logs and smoke artifacts retained for human review.',
      'external_state_created':'NONE','external_cleanup_required':'false'})
cleanup_rows.append({'candidate_id':'lab','candidate':'O03 lab root','lab_paths':str(LAB),'process_state':'NO_TRACKED_BACKGROUND_PROCESS','bound_ports':'NONE','cleanup_command':"rm -rf '"+str(LAB)+"'",'cleanup_executed':'false','cleanup_verified':'NO_DAEMON_OR_LISTENER_REMAINS; evidence retained','retention_reason':'Run logs, fixtures, exact source snapshots and outputs retained until review.','external_state_created':'NONE','external_cleanup_required':'false'})

def write_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

write_csv(OUT/'candidate-inventory.csv',inv_fields,inv_rows)
write_csv(OUT/'license-and-security.csv',lic_fields,lic_rows)
write_csv(OUT/'deployment-smoke-results.csv',smoke_fields,smoke_rows)
write_csv(OUT/'resource-profile.csv',res_fields,res_rows)
write_csv(OUT/'contract-fit.csv',contract_fields,contract_rows)
write_csv(OUT/'cleanup-manifest.csv',cleanup_fields,cleanup_rows)

# Report.
report=f'''---
type: architecture-report
status: complete
date: 2026-07-14
program: Helixar World-Class Benchmark Program
lane: O03
strategic_track:
  - shared-platform
  - demand-authority
  - video-intelligence
---

# O03 Web, Market and Voice OSS Adoption Report

## Verdict

**Bounded O03 lab: PASS. Production or integration readiness: NOT PROVEN.**

All **15/15 assigned candidates** were fetched as exact git snapshots, source/license inspected, and classified. Four compact localhost/synthetic smoke slices passed: **Lighthouse, Mozilla Readability, Splink, and OpenAI Whisper**. Every smoke used synthetic or localhost input; offline final runs denied network for Readability, Splink, and Whisper, while Lighthouse was limited to a loopback fixture on `127.0.0.1:18731`. No customer data, credentials, production connector, external write, implementation-repository edit, or live publishing/ads/CRM target was used.

The outputs prove only bounded component behavior. They do **not** prove production security, integration fit, source rights, consent/deletion compliance, crawler choice, ASR accuracy across languages/noise, entity-resolution precision, or end-to-end Helixar contract compatibility.

## Acceptance summary

| Gate | Result | Evidence |
|---|---:|---|
| Assigned candidate coverage | **15/15 PASS** | Exact commits and archive hashes in `candidate-inventory.csv` |
| Minimum compact smoke slices | **4 PASS** | Lighthouse, Readability, Splink, Whisper |
| Integration fit claimed | **0** | Every row explicitly `integration_fit_proven=false` |
| Production suitability claimed | **0** | Every row explicitly `production_suitability=UNKNOWN` |
| License/security inventory | **15/15 PASS for source inspection** | Root license file paths and SHA-256 values recorded |
| Offline/loopback runtime boundary | **PASS** | 3 network-denied runs; 1 loopback-only audit |
| Resource limit | **PASS** | Lab {lab_bytes:,} bytes; no file >2 GB; total <10 GB |
| Cleanup/reversibility | **PASS** | No retained service/listener; disposable evidence retained with exact deletion commands |
| Implementation repositories | **PASS** | Four explicit Helixar roots rechecked clean and unchanged at completion |

## Candidate decisions

| Candidate | Lane | Bounded result | Classification | Decision boundary |
|---|---|---|---|---|
'''
for n in names:
    bounded='PASS fixture' if passed[n] else 'Source/license inspected; runtime NOT_RUN'
    report += f"| {display[n]} | {lane[n]} | {bounded} | **{classification[n]}** | {next_gate[n]} |\n"
report += f'''

## Smoke evidence

### Lighthouse — `ADOPT` behind a Helixar audit adapter

Selected source commit `{meta['lighthouse']['commit']}`. A local static page was served only on `127.0.0.1:18731`; Lighthouse 13.4.0 completed accessibility, best-practices and SEO categories. Final structural assertions passed with category scores **1.00 / 0.96 / 1.00**. The web server was terminated. Runtime was **{fixture_duration['lighthouse']} s**, peak RSS **{peak_rss['lighthouse']:,} bytes**. This does not select a site-wide crawler or prove stable performance metrics.

### Mozilla Readability — `ADAPT`

Selected source commit `{meta['readability']['commit']}`. The synthetic HTML extraction was byte-repeatable and retained the expected title and body while excluding unrelated link text. Final run passed under macOS network-deny sandbox in **{fixture_duration['readability']} s**, peak RSS **{peak_rss['readability']:,} bytes**. Extraction is not permission to ingest, retain, or redistribute content; the adapter must bind output to a permitted raw snapshot hash.

### Splink — `ADAPT` as candidate generator only

Selected source commit `{meta['splink']['commit']}`. The synthetic entity fixture returned only blocked pair `r1/r2`, probability `0.6735395189`, repeated exactly, did not mutate input, and performed no merge/write. Final run passed under network deny in **{fixture_duration['splink']} s**, peak RSS **{peak_rss['splink']:,} bytes**. A labeled benchmark and reversible human `AliasDecision` remain mandatory.

### OpenAI Whisper — `ADAPT` as machine-candidate ASR

Selected code commit `{meta['whisper']['commit']}` with local `tiny.en` model SHA-256 `d3dd57d32accea0b295c96e26691aa14d8822fac7d9d27d5dc00b4ca2826dd03`. A synthetic macOS-voice fixture transcribed exactly and repeatably with segment and word timecodes. Final run passed under network deny in **{fixture_duration['whisper']} s**, peak RSS **{peak_rss['whisper']:,} bytes**. The transcript remains a machine candidate; speaker identity, consent, deletion, diarization, bias, and quote truth are not provided by Whisper.

## Source-rights, consent, deletion, and provenance boundary

The lab preserves the architecture packets' non-negotiable contracts:

1. **R03 / web authority:** no collection without a versioned source registry entry. Rights/terms and robots policy are distinct; robots compliance is required but is not legal authorization. A proposal must resolve to a `PageSnapshot` with fetch time, hash, canonical/robots state, and artifact pointer.
2. **R04 / market evidence:** rights precede ingestion; denied, missing, expired, or conflicting rights disable the source. Raw observations, hashes, claims, entity candidates, and analyst decisions are append-only. A probabilistic match can never silently overwrite or merge a canonical entity.
3. **R05 / voice and pain evidence:** an exact `QuoteSpan` with offsets/timecodes and transformation lineage is the evidence primitive, not a summary. Study purpose, consent, retention, withdrawal/deletion state, reporter pseudonym, model/version, and review state must be retained. Derived transcripts and themes must be deletable/revocable with their source artifact policy.
4. **Authority:** OSS tools may collect, extract, score, transcribe, or suggest. Helixar retains source permission, canonical storage, approval, taxonomy activation, external-write authority, decision receipts, and rollback.

## License and security findings

- Root licenses were inspected from the selected source snapshots and hashed for every candidate.
- Lighthouse core is Apache-2.0 but contains bundled third-party notices; redistribution requires a component/notice inventory.
- Taguette core is BSD-3-Clause, while its installer notice references GPL-3.0 Calibre; the installer is not cleared for embedding.
- Formbricks is mixed **AGPL-3.0 core plus enterprise licensing**. Classification is `PARTNER`; no code copying or embedding is authorized without legal review.
- Offline npm audit reported zero known vulnerabilities for the installed Lighthouse and Readability dependency trees at this snapshot. Isolated `pip check` passed for Splink and Whisper, but no CVE scanner or transitive legal review was run for those Python environments.
- Production security suitability remains `UNKNOWN` for all candidates.

## Failed attempts and corrections

The process ledger intentionally retains failed attempts. Lighthouse first hit peer-dependency and missing generated-report assets before the exact source tree was installed/built successfully. Splink required API-fixture corrections and `pyarrow`; the final run passed. The initial macOS voice synthesis format option failed; the corrected synthesis and WAV conversion passed. Early `pip check` failures were traced to inherited `PYTHONPATH`; isolated checks passed. Early corpus-freeze retries failed on script assumptions; the fifth corrected run succeeded. These failures are evidence, not hidden.

Process ledger totals at report generation: **{len(proc)} recorded commands**, **{sum(1 for r in proc if r.get('exit_code')==0)} success**, **{sum(1 for r in proc if r.get('exit_code') not in (0,None))} nonzero attempts**; network ledger: **{len(net)} declared fetches**, **{sum(1 for r in net if r.get('exit_code')==0)} success**, **{sum(1 for r in net if r.get('exit_code') not in (0,None))} nonzero attempts**.

## Resource and operations assessment

- Total disposable lab: **{lab_bytes:,} bytes**; no single file exceeds 2 GB.
- Largest tested RSS: Whisper **{peak_rss['whisper']:,} bytes**.
- Lighthouse used one transient loopback listener; every other final fixture used no port.
- No persistent services, databases, Docker stacks, external accounts, browser profiles, or production credentials were created.
- The lab root is the deletion boundary. Exact per-candidate and whole-lab cleanup commands are in `cleanup-manifest.csv`.

## Build vs partner vs adopt

| Decision | Components | Rationale |
|---|---|---|
| **Adopt** | Lighthouse | Commodity, inspectable audit engine with successful localhost proof; keep Helixar rights, evidence and action contracts above it. |
| **Adapt** | Readability, Splink, Whisper | Small replaceable ports passed bounded fixtures; each lacks a required Helixar governance layer. |
| **Partner / isolate** | Formbricks | Survey delivery may be useful, but mixed licensing and participant-data governance block code adoption. |
| **POC more** | Crawlee, Unlighthouse, SiteOne, changedetection.io, OpenRefine, dedupe, Taguette, doccano, Argilla, BERTopic | Source relevance exists, but runtime/component choice, operational value, or contract fit is unproven. |
| **Build in Helixar** | Rights/consent registry, immutable snapshots/artifacts, alias and taxonomy decisions, quote/timecode lineage, deletion propagation, approvals, receipts, adapters | These are Helixar's authority and compounding-memory core; no evaluated OSS component owns them safely. |

## Explicit unresolved decisions

1. Select **Crawlee vs SiteOne vs no separate crawler** only after one identical robots/rate/provenance/export fixture; Unlighthouse is optional after that.
2. Define and approve the canonical source-rights/robots/terms record and retention classes before any live-web adapter.
3. Set entity-resolution labeled benchmark, precision/recall thresholds, reviewer workflow, and rollback semantics before Splink leaves synthetic fixtures.
4. Approve voice consent, storage, withdrawal/deletion propagation, language/noise benchmark, and human-review policy before Whisper sees governed media.
5. Decide whether Formbricks is worth procurement/API isolation; code adoption remains blocked pending legal review.
6. Confirm component owners and patch/CVE cadence for every adopted adapter.

## Evidence index

- [[05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice/candidate-inventory.csv]]
- [[05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice/license-and-security.csv]]
- [[05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice/deployment-smoke-results.csv]]
- [[05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice/resource-profile.csv]]
- [[05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice/contract-fit.csv]]
- [[05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O03-web-market-voice/cleanup-manifest.csv]]
- [[04_Logs/Runs/2026-07-14 - O03 Web Market and Voice OSS Lab Run Receipt]]
- Lab root: `{LAB}`
'''
ARCH.write_text(report)

# Artifact hashes and receipt.
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
artifacts=[ARCH]+[OUT/x for x in ['candidate-inventory.csv','license-and-security.csv','deployment-smoke-results.csv','resource-profile.csv','contract-fit.csv','cleanup-manifest.csv']]
receipt='''---
type: run-receipt
status: complete
date: 2026-07-14
program: Helixar World-Class Benchmark Program
lane: O03
---

# O03 Web Market and Voice OSS Lab Run Receipt

## Outcome

**PASS for bounded localhost/synthetic OSS evaluation. Integration and production readiness remain unproven.**

- Assigned candidates inspected: **15/15**
- Compact smoke slices passed: **4/4 selected** — Lighthouse, Readability, Splink, Whisper
- Candidate classifications: **1 ADOPT, 3 ADAPT, 1 PARTNER, 10 POC_MORE**
- Integration-fit claims: **0**
- Production-suitability claims: **0**
- Customer data, secrets, live connectors or external writes: **none**

## Safety and integrity

- Disposable root: `'''+str(LAB)+'''`
- Final runtime boundary: three network-denied fixtures plus one loopback-only Lighthouse audit.
- Residual lab listeners/services: none observed before finalization.
- Lab size at generation: **'''+f'{lab_bytes:,}'+''' bytes**; files over 2 GB: **'''+str(len(large_files))+'''**.
- Four Helixar implementation repositories were rechecked at their exact roots and were clean/unmodified at completion.

## Implementation repository hashes

| Repository | HEAD | Dirty rows |
|---|---|---:|
| organic-authority | `de01b251500e9b9d458853c6d45927ca51fc6e0e` | 0 |
| demand-intelligence | `9eaf29868818775e669ed79ba8cf857adfbf40f5` | 0 |
| content-distribution | `c8cd2e2bfe797ba8401db523ecbe7872f984d284` | 0 |
| revenue-pipeline | `66d9f0a6925a1b56cd953ae2f9bec6643948601a` | 0 |

## Run ledger

- Recorded commands before artifact generation: **'''+str(len(proc))+'''**
- Successful command attempts: **'''+str(sum(1 for r in proc if r.get('exit_code')==0))+'''**
- Nonzero command attempts retained: **'''+str(sum(1 for r in proc if r.get('exit_code') not in (0,None)))+'''**
- Declared network fetches: **'''+str(len(net))+'''**; successful **'''+str(sum(1 for r in net if r.get('exit_code')==0))+'''**, nonzero **'''+str(sum(1 for r in net if r.get('exit_code') not in (0,None)))+'''**
- Process log: `'''+str(LAB/'process-log.jsonl')+'''`
- Network log: `'''+str(LAB/'network-log.jsonl')+'''`
- Service log: `'''+str(LAB/'service-log.jsonl')+'''`

## Output hashes

| Artifact | SHA-256 |
|---|---|
'''
for p in artifacts:
    receipt += f'| `{p}` | `{sha(p)}` |\n'
receipt += '''
## Cleanup state

No candidate service remains running. Exact per-candidate and whole-lab deletion commands are recorded in `cleanup-manifest.csv`. Evidence is intentionally retained in the disposable root for review; deletion was not executed.

## Linked report

- [[02_Projects/Helixar World-Class Benchmark Program/Architecture/10 O03 Web Market and Voice OSS Adoption Report]]
'''
RECEIPT.write_text(receipt)

summary={'generated_at':datetime.now(timezone.utc).isoformat(),'candidate_count':len(names),'smoke_pass_count':sum(passed.values()),'classification_counts':dict(Counter(classification.values())),'process_count_before_generation':len(proc),'network_fetch_count':len(net),'lab_bytes':lab_bytes,'large_files_over_2gb':large_files,'outputs':{str(p):sha(p) for p in artifacts+[RECEIPT]}}
(LAB/'final-summary.json').write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
