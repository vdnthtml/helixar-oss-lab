#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, re, subprocess
from pathlib import Path
LAB=Path('/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust')
DYS=Path('/Users/vedantswami/Projects/Dystopia/Dystopia')
OUT=DYS/'05_Data/Helixar World-Class Benchmark Program/Open Source Deployment Research/O01-control-trust'
REPORT=DYS/'02_Projects/Helixar World-Class Benchmark Program/Architecture/O01 Control Plane, Trust and Observability OSS Lab Report.md'
expected=['candidate-inventory.csv','license-and-security.csv','deployment-smoke-results.csv','resource-profile.csv','contract-fit.csv','cleanup-manifest.csv']
ids={'temporal','langgraph','trigger-dev','prefect','opa','cedar','openfga','opentelemetry','openinference','promptfoo','inspect-ai','langfuse','phoenix','giskard','pyrit','garak','presidio'}
checks=[]
def check(name, cond, detail=''):
    checks.append({'check':name,'status':'PASS' if cond else 'FAIL','detail':detail})
def rows(name):
    with (OUT/name).open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
check('report_exists_nonempty',REPORT.exists() and REPORT.stat().st_size>5000,str(REPORT))
for name in expected: check(f'{name}_exists_nonempty',(OUT/name).exists() and (OUT/name).stat().st_size>20,str(OUT/name))
inv=rows('candidate-inventory.csv'); lic=rows('license-and-security.csv'); smoke=rows('deployment-smoke-results.csv'); res=rows('resource-profile.csv'); fit=rows('contract-fit.csv'); clean=rows('cleanup-manifest.csv')
for label,data in [('inventory',inv),('license',lic),('resource',res),('contract',fit)]:
    got={x['candidate_id'] for x in data}; check(f'{label}_17_unique',len(data)==17 and got==ids,f'rows={len(data)} unique={len(got)}')
check('cleanup_17_plus_lab',len(clean)==18 and {x['candidate_id'] for x in clean}==ids|{'lab'},f'rows={len(clean)}')
check('smoke_accounts_all_candidates',{x['candidate_id'] for x in smoke}==ids,f'rows={len(smoke)}')
check('inventory_stage_distinctions',all(x['source_inspected']=='true' and x['integration_fit_proven']=='false' and x['production_suitability_unknown']=='true' for x in inv))
allowed={'ADOPT','ADAPT','POC_MORE','PARTNER','REJECT_LICENSE','REJECT_OPERATIONS','REJECT_FIT','NOT_RUN'}
check('classification_enum',all(x['classification'] in allowed for x in inv))
check('exact_git_hashes',all(re.fullmatch(r'[0-9a-f]{40}',x['selected_commit']) for x in inv))
check('exact_license_hashes',all(re.fullmatch(r'[0-9a-f]{64}',x['license_sha256']) for x in lic))
check('opa_release_commit',next(x for x in inv if x['candidate_id']=='opa')['selected_commit']=='e695c9ef8edb0f8b9f13d014d7bc8a7fbcc57297')
passes=[x for x in smoke if x['status']=='PASS']
check('every_pass_has_command_output_evidence',all(x['command']!='NOT_RUN' and x['real_output'] and Path(x['evidence']).exists() for x in passes),f'pass_rows={len(passes)}')
check('orchestrator_pass',any(x['candidate_id']=='langgraph' and x['status']=='PASS' for x in smoke))
check('policy_pass',any(x['candidate_id']=='opa' and x['status']=='PASS' for x in smoke))
check('two_eval_observability_pass',len({x['candidate_id'] for x in smoke if x['candidate_id'] in {'opentelemetry','promptfoo','presidio'} and x['status']=='PASS'})>=2)
check('final_smokes_network_denied',all(x['network_runtime']=='DENIED_BY_SANDBOX_AND_PASS' for x in passes))
check('no_bound_ports_csv',all(x['ports']=='NONE' for x in smoke) and all(x['bound_ports']=='NONE' for x in res+clean))
check('no_external_state_cleanup',all(x['external_state_created']=='NONE' for x in clean))
check('phoenix_license_block',next(x for x in inv if x['candidate_id']=='phoenix')['classification']=='REJECT_LICENSE')
check('production_unknown_contracts',all(x['production_suitability']=='UNKNOWN' for x in fit))
# Recompute root license hashes for exact selected source evidence. OPA selected-tag license is separately retained.
for x in lic:
    key=x['candidate_id']; p=LAB/'inspected'/key/('LICENSE-v1.18.2' if key=='opa' else 'LICENSE')
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    check(f'license_hash_{key}',actual==x['license_sha256'],str(p))
# Process/listener check: exact commands are recorded by the outer lab harness.
ps=subprocess.run(['/bin/ps','-axo','pid=,command='],text=True,capture_output=True,check=True).stdout
live=[line.strip() for line in ps.splitlines() if 'O01-control-trust' in line and not any(tok in line for tok in ['validate_deliverables.py','labrun.py --candidate VALIDATION'])]
check('no_live_lab_candidate_process',not live,' | '.join(live[:5]))
lsof=subprocess.run(['/usr/sbin/lsof','-nP','-iTCP','-sTCP:LISTEN'],text=True,capture_output=True).stdout
# Candidate binaries have distinctive command names; no service was launched by this lane.
listener_lines=[line for line in lsof.splitlines() if re.search(r'(^|\s)(opa|promptfoo|temporal|prefect)(\s|$)',line,re.I)]
check('no_candidate_listener',not listener_lines,' | '.join(listener_lines[:5]))
# Hash all deliverables generated so far.
files=[REPORT]+[OUT/x for x in expected]
hashes={str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks,'hashes':hashes,'row_counts':{'candidate_inventory':len(inv),'license_security':len(lic),'deployment_smoke':len(smoke),'resource_profile':len(res),'contract_fit':len(fit),'cleanup_manifest':len(clean)},'pass_smoke_rows':len(passes),'live_lab_process_matches':live,'candidate_listener_matches':listener_lines}
(LAB/'validation-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='PASS' else 1)
