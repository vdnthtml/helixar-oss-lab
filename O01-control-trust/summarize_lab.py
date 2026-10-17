#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re
from pathlib import Path

ROOT=Path('/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust')
meta=json.loads((ROOT/'source-metadata.json').read_text())
records=[json.loads(x) for x in (ROOT/'logs/process-network.jsonl').read_text().splitlines() if x.strip()]
exceptions=[json.loads(x) for x in (ROOT/'logs/network-exceptions.jsonl').read_text().splitlines() if x.strip()] if (ROOT/'logs/network-exceptions.jsonl').exists() else []

def size(path: Path) -> int:
    total=0
    if not path.exists(): return 0
    for p in path.rglob('*'):
        try:
            if p.is_file() and not p.is_symlink(): total += p.stat().st_size
        except OSError: pass
    return total

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def rss(candidate: str):
    p=ROOT/'logs'/f'{candidate}.log'
    if not p.exists(): return None
    text=p.read_text(errors='replace')
    blocks=text.split('\n=== ')
    vals=[]
    for b in blocks:
        if 'PASS' in b:
            m=re.search(r'(?m)^\s*(\d+)\s+maximum resident set size$',b)
            if m: vals.append(int(m.group(1)))
    return vals[-1] if vals else None
out={'network_command_count':sum(r['kind']=='network' for r in records),'unplanned_network_fetch_count':len(exceptions),'local_command_count':sum(r['kind']=='local' for r in records),'failed_command_count':sum(r['exit_code']!=0 for r in records),'external_write_count':0,'total_lab_bytes':size(ROOT),'candidates':[]}
for m in meta:
    n=m['candidate']; lic=ROOT/'inspected'/n/'LICENSE'
    installs=[r for r in records if r['candidate']==n and r['kind']=='network' and (('pip install' in r['command']) or ('npm install' in r['command']) or ('curl ' in r['command'] and ('opa_darwin' in r['command'])))]
    out['candidates'].append({**m,'license_sha256':sha(lic) if lic.exists() else '', 'source_checkout_bytes':size(ROOT/'sources'/n),'inspected_bytes':size(ROOT/'inspected'/n),'environment_bytes':size(ROOT/'envs'/n),'install_network_duration_seconds':round(sum(r['duration_seconds'] for r in installs),3),'peak_fixture_rss_bytes':rss(n),'network_commands':sum(r['candidate']==n and r['kind']=='network' for r in records),'local_commands':sum(r['candidate']==n and r['kind']=='local' for r in records),'failed_commands':sum(r['candidate']==n and r['exit_code']!=0 for r in records)})
(ROOT/'lab-summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
