#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path('/Users/vedantswami/Projects/helixar-oss-labs/O01-control-trust')
RUN = ROOT / 'labrun.py'
REPOS = {
    'temporal': 'https://github.com/temporalio/temporal.git',
    'langgraph': 'https://github.com/langchain-ai/langgraph.git',
    'trigger-dev': 'https://github.com/triggerdotdev/trigger.dev.git',
    'prefect': 'https://github.com/PrefectHQ/prefect.git',
    'opa': 'https://github.com/open-policy-agent/opa.git',
    'cedar': 'https://github.com/cedar-policy/cedar.git',
    'openfga': 'https://github.com/openfga/openfga.git',
    'opentelemetry': 'https://github.com/open-telemetry/opentelemetry-specification.git',
    'openinference': 'https://github.com/Arize-ai/openinference.git',
    'promptfoo': 'https://github.com/promptfoo/promptfoo.git',
    'inspect-ai': 'https://github.com/UKGovernmentBEIS/inspect_ai.git',
    'langfuse': 'https://github.com/langfuse/langfuse.git',
    'phoenix': 'https://github.com/Arize-ai/phoenix.git',
    'giskard': 'https://github.com/Giskard-AI/giskard-oss.git',
    'pyrit': 'https://github.com/microsoft/PyRIT.git',
    'garak': 'https://github.com/NVIDIA/garak.git',
    'presidio': 'https://github.com/data-privacy-stack/presidio.git',
}
SMOKE = {'langgraph', 'opa', 'promptfoo', 'opentelemetry', 'presidio'}

def run(candidate: str, kind: str, cwd: Path, argv: list[str], url: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(RUN), '--candidate', candidate, '--kind', kind]
    if url:
        cmd += ['--url', url]
    cmd += ['--cwd', str(cwd), '--'] + argv
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and p.returncode:
        print(p.stdout, file=sys.stderr)
        raise SystemExit(f'{candidate}: command failed: {argv}')
    return p

src = ROOT / 'sources'
src.mkdir(parents=True, exist_ok=True)
meta = []
for name, url in REPOS.items():
    dest = src / name
    if not dest.exists():
        run(name, 'network', ROOT, ['git', 'clone', '--depth', '1', '--filter=blob:none', '--no-checkout', url, str(dest)], url)
    commit = run(name, 'local', dest, ['git', 'rev-parse', 'HEAD']).stdout.strip().splitlines()[-1]
    branch = run(name, 'local', dest, ['git', 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD'], check=False).stdout.strip().splitlines()
    files_out = run(name, 'local', dest, ['git', 'ls-tree', '-r', '--name-only', 'HEAD']).stdout
    files = [x.strip() for x in files_out.splitlines() if x.strip() and not x.startswith('===')]
    license_paths = [p for p in files if Path(p).name.lower() in {'license','license.md','license.txt','license-mit','license-apache','copying'}]
    if not license_paths:
        license_paths = [p for p in files if 'license' in Path(p).name.lower()][:10]
    inspect_paths = []
    for preferred in ['README.md','pyproject.toml','package.json','go.mod','Cargo.toml']:
        if preferred in files:
            inspect_paths.append(preferred)
    inspect_paths += license_paths[:10]
    seen = set(); inspect_paths = [p for p in inspect_paths if not (p in seen or seen.add(p))]
    inspected = []
    for path in inspect_paths:
        out_path = ROOT / 'inspected' / name / path.replace('/', '__')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result = run(name, 'network', dest, ['git', 'show', f'HEAD:{path}'], url, check=False)
        if result.returncode == 0:
            # labrun output is command stdout only; preserve exact inspected content.
            out_path.write_text(result.stdout, encoding='utf-8')
            inspected.append(path)
    if name in SMOKE:
        run(name, 'network', dest, ['git', 'checkout', '--detach', 'HEAD'], url)
    meta.append({'candidate': name, 'repository': url.removesuffix('.git'), 'commit': commit, 'default_branch_ref': branch[-1] if branch else '', 'license_paths': license_paths, 'inspected_paths': inspected, 'smoke_checkout': name in SMOKE})
(ROOT / 'source-metadata.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
print(json.dumps(meta, indent=2))
