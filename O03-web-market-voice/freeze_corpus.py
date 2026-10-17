#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil

LAB = Path("/Users/vedantswami/Projects/helixar-oss-labs/O03-web-market-voice")
DYS = Path("/Users/vedantswami/Projects/Dystopia/Dystopia")
OUT = DYS / "05_Data/Helixar World-Class Benchmark Program/O03 Web Market and Voice OSS Lab/source-corpus-manifest.csv"
FROZEN = LAB / "frozen-inputs/2026-07-14"
FROZEN.mkdir(parents=True, exist_ok=True)

for name in ("process-log.jsonl", "network-log.jsonl", "service-log.jsonl", "source-metadata.json"):
    shutil.copy2(LAB / name, FROZEN / name)

paths = [
    DYS / "000_HOME.md",
    DYS / "05_Data/Current State/Dystopia Current Snapshot.md",
    DYS / "04_Logs/Daily/Daily Log - 2026-07-14.md",
    DYS / "02_Projects/Helixar World-Class Benchmark Program/Hermes Launch Prompts/Wave A/O03 Web Market and Voice OSS Lab.md",
    DYS / "02_Projects/Helixar World-Class Benchmark Program/00 Helixar World-Class Benchmark Program - Control Center.md",
    DYS / "02_Projects/Helixar World-Class Benchmark Program/02 Current Architecture Benchmark.md",
    DYS / "02_Projects/Helixar World-Class Benchmark Program/04 Cross-Packet Implementation Readiness Audit - 2026-07-14.md",
    DYS / "02_Projects/Helixar World-Class Benchmark Program/05 Hermes Parallel Architecture and Build Roadmap.md",
    DYS / "02_Projects/Helixar World-Class Benchmark Program/06 Folder and Evidence Use Guide.md",
    Path("/Users/vedantswami/.hermes/skills/software-development/integration-readiness-audit/SKILL.md"),
    Path("/Users/vedantswami/.hermes/skills/software-development/integration-readiness-audit/references/oss-deployability-lab.md"),
]
for packet in ("R03 Terra-Authority", "R04 Terra-Market", "R05 Terra-Pain"):
    for name in ("open-source-inventory.csv", "evidence-ledger.csv"):
        paths.append(DYS / f"05_Data/Helixar World-Class Benchmark Program/{packet}/{name}")
paths += [
    FROZEN / "source-metadata.json",
    FROZEN / "process-log.jsonl",
    FROZEN / "network-log.jsonl",
    FROZEN / "service-log.jsonl",
    LAB / "fixtures/web/index.html",
    LAB / "fixtures/voice-fixture.wav",
    LAB / "candidates/readability/smoke.mjs",
    LAB / "candidates/splink/smoke.py",
    LAB / "candidates/whisper/smoke.py",
    LAB / "lighthouse_smoke.py",
    LAB / "artifacts/readability/summary.json",
    LAB / "artifacts/splink/summary.json",
    LAB / "artifacts/whisper/summary.json",
    LAB / "artifacts/lighthouse/summary.json",
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

now = dt.datetime.now(dt.timezone.utc).isoformat()
rows: list[dict[str, str | int]] = []
for p in paths:
    if not p.is_file():
        raise FileNotFoundError(p)
    role = "governing_or_context_document"
    if p.parent == FROZEN:
        role = "frozen_execution_or_provenance_evidence"
    elif "artifacts" in p.parts:
        role = "smoke_result"
    elif "fixtures" in p.parts:
        role = "synthetic_fixture"
    elif p.name.startswith("smoke") or p.name == "lighthouse_smoke.py":
        role = "test_harness"
    rows.append({
        "corpus_id": "O03-2026-07-14-final-analysis",
        "item_type": "file",
        "absolute_path_or_source": str(p),
        "bytes": p.stat().st_size,
        "sha256": sha(p),
        "immutable_ref": "sha256",
        "role": role,
        "frozen_at_utc": now,
    })
metadata = json.loads((FROZEN / "source-metadata.json").read_text())
for c in metadata:
    rows.append({
        "corpus_id": "O03-2026-07-14-final-analysis",
        "item_type": "git_source_archive",
        "absolute_path_or_source": c["repository"],
        "bytes": int(c["disk_kb"]) * 1024,
        "sha256": c["archive_sha256"],
        "immutable_ref": c["commit"],
        "role": "candidate_source_tree",
        "frozen_at_utc": now,
    })
    for lic in c["license_files"]:
        lp = LAB / "repos" / c["name"] / lic["path"]
        if not lp.is_file() or sha(lp) != lic["sha256"]:
            raise RuntimeError(f"license integrity mismatch: {lp}")
        rows.append({
            "corpus_id": "O03-2026-07-14-final-analysis",
            "item_type": "license_file",
            "absolute_path_or_source": str(lp),
            "bytes": lp.stat().st_size,
            "sha256": lic["sha256"],
            "immutable_ref": c["commit"],
            "role": "license_evidence",
            "frozen_at_utc": now,
        })
# Explicitly add Formbricks' deeper enterprise license scope, which is not in the shallow metadata scan.
ee = LAB / "repos/formbricks/apps/web/modules/ee/LICENSE"
rows.append({
    "corpus_id": "O03-2026-07-14-final-analysis",
    "item_type": "license_file",
    "absolute_path_or_source": str(ee),
    "bytes": ee.stat().st_size,
    "sha256": sha(ee),
    "immutable_ref": next(c["commit"] for c in metadata if c["name"] == "formbricks"),
    "role": "enterprise_license_scope_evidence",
    "frozen_at_utc": now,
})
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps({"output": str(OUT), "rows": len(rows), "frozen_inputs": str(FROZEN)}, indent=2))
