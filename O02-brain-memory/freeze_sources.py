#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import pathlib

VAULT = pathlib.Path('/Users/vedantswami/Projects/Dystopia/Dystopia')
ROOT = pathlib.Path(__file__).resolve().parent
MANDATORY = [
    VAULT / 'AGENTS.md',
    VAULT / '000_HOME.md',
    VAULT / '05_Data/Current State/Dystopia Current Snapshot.md',
    VAULT / '04_Logs/Daily/Daily Log - 2026-07-14.md',
    VAULT / '02_Projects/Helixar World-Class Benchmark Program/00 Helixar World-Class Benchmark Program - Control Center.md',
    VAULT / '02_Projects/Helixar World-Class Benchmark Program/02 Current Architecture Benchmark.md',
    VAULT / '02_Projects/Helixar World-Class Benchmark Program/04 Cross-Packet Implementation Readiness Audit - 2026-07-14.md',
    VAULT / '02_Projects/Helixar World-Class Benchmark Program/05 Hermes Parallel Architecture and Build Roadmap.md',
    VAULT / '02_Projects/Helixar World-Class Benchmark Program/06 Folder and Evidence Use Guide.md',
    VAULT / '02_Projects/Helixar World-Class Benchmark Program/Packets/R01 Sol-Fleet Research and Architecture Packet.md',
]
DATA_ROOT = VAULT / '05_Data/Helixar World-Class Benchmark Program'
TERMS = ('letta', 'mem0', 'graphiti', 'llamaindex', 'unstructured', 'pgvector', 'qdrant', 'minio', 'postgresql')


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

files = list(MANDATORY)
rows = []
for lane in sorted(DATA_ROOT.glob('R?? *')):
    for name in ('open-source-inventory.csv', 'evidence-ledger.csv'):
        path = lane / name
        if not path.exists():
            continue
        files.append(path)
        with path.open(newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            matches = []
            for rownum, row in enumerate(reader, start=2):
                count += 1
                flattened = json.dumps(row, ensure_ascii=False).lower()
                if any(term in flattened for term in TERMS):
                    matches.append({'row_number': rownum, 'row': row})
            rows.append({
                'path': str(path),
                'row_count': count,
                'headers': reader.fieldnames,
                'candidate_matches': matches,
            })
manifest = []
for path in files:
    manifest.append({
        'path': str(path),
        'sha256': digest(path),
        'bytes': path.stat().st_size,
        'role': 'mandatory_context' if path in MANDATORY else 'source_csv',
    })
(ROOT / 'source-hash-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
(ROOT / 'source-csv-inspection.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({
    'files_hashed': len(manifest),
    'source_csvs_read': len(rows),
    'source_csv_rows_read': sum(item['row_count'] for item in rows),
    'candidate_match_rows': sum(len(item['candidate_matches']) for item in rows),
    'manifest': str(ROOT / 'source-hash-manifest.json'),
    'inspection': str(ROOT / 'source-csv-inspection.json'),
}, indent=2))
