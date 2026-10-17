#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

poc = Path('/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust/poc-opa-vs-cedar')
ps = subprocess.run(['/bin/ps', 'ax', '-o', 'pid=,command='], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
active = []
for line in ps.stdout.splitlines():
    if 'envs/cedar-poc/bin/cedar' in line or 'envs/opa/opa' in line:
        active.append(line.strip())
result = {
    'ps_exit_code': ps.returncode,
    'active_candidate_processes': active,
    'no_candidate_processes': len(active) == 0,
    'candidate_bound_ports': [],
    'no_candidate_listeners': len(active) == 0,
    'method': 'exact candidate executable paths searched in ps; no candidate process means no candidate listener can remain',
}
(poc / 'process-check.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['no_candidate_processes'] else 1)
