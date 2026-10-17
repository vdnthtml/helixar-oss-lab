#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
REPOS = {
    'Letta': ROOT / 'repos/letta',
    'Letta current (letta-code)': ROOT / 'repos/letta-code',
    'Mem0': ROOT / 'repos/mem0',
    'Graphiti': ROOT / 'repos/graphiti',
    'LlamaIndex': ROOT / 'repos/llama_index',
    'Unstructured': ROOT / 'repos/unstructured',
    'PostgreSQL+pgvector': ROOT / 'repos/pgvector',
    'Qdrant': ROOT / 'repos/qdrant',
    'MinIO': ROOT / 'repos/minio',
}


def git(path: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

records = []
for name, path in REPOS.items():
    license_files = []
    for candidate in sorted(path.glob('LICENSE*')) + sorted(path.glob('COPYING*')):
        if candidate.is_file():
            license_files.append({
                'path': str(candidate.relative_to(path)),
                'sha256': sha256(candidate),
                'bytes': candidate.stat().st_size,
                'first_line': candidate.read_text(encoding='utf-8', errors='replace').splitlines()[0] if candidate.stat().st_size else '',
            })
    manifests = []
    for filename in ('pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod', 'Makefile', 'README.md', 'SECURITY.md', 'SECURITY'):
        candidate = path / filename
        if candidate.exists() and candidate.is_file():
            manifests.append({
                'path': filename,
                'sha256': sha256(candidate),
                'bytes': candidate.stat().st_size,
            })
    origin = git(path, 'remote', 'get-url', 'origin')
    commit = git(path, 'rev-parse', 'HEAD')
    record = {
        'candidate': name,
        'path': str(path),
        'repository_url': origin,
        'commit': commit,
        'tree_hash': git(path, 'rev-parse', f'{commit}^{{tree}}'),
        'commit_timestamp': git(path, 'show', '-s', '--format=%cI', commit),
        'commit_subject': git(path, 'show', '-s', '--format=%s', commit),
        'branch': git(path, 'branch', '--show-current'),
        'shallow': git(path, 'rev-parse', '--is-shallow-repository'),
        'license_files': license_files,
        'manifests': manifests,
    }
    records.append(record)

out = ROOT / 'candidate-source-manifest.json'
out.write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'candidates': len(records), 'manifest': str(out)}, indent=2))
for record in records:
    print(f"{record['candidate']}|{record['commit']}|{record['tree_hash']}|{record['commit_timestamp']}|{record['license_files']}")
