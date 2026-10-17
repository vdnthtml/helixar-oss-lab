#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import torch
import whisper

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "fixtures" / "voice-fixture.wav"
MODEL = ROOT / "candidates" / "whisper" / "models" / "tiny.en.pt"
OUT = ROOT / "artifacts" / "whisper"
OUT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(result: dict) -> dict:
    return {
        "text": " ".join(result["text"].split()),
        "language": result["language"],
        "segments": [
            {
                "id": int(s["id"]),
                "start": round(float(s["start"]), 3),
                "end": round(float(s["end"]), 3),
                "text": " ".join(s["text"].split()),
                "words": [
                    {
                        "word": w["word"],
                        "start": round(float(w["start"]), 3),
                        "end": round(float(w["end"]), 3),
                    }
                    for w in s.get("words", [])
                ],
            }
            for s in result["segments"]
        ],
    }


def transcribe(model) -> dict:
    return normalize(
        model.transcribe(
            str(AUDIO),
            language="en",
            task="transcribe",
            fp16=False,
            temperature=0,
            beam_size=1,
            word_timestamps=True,
            condition_on_previous_text=False,
            verbose=False,
        )
    )


started = time.monotonic()
model = whisper.load_model("tiny.en", device="cpu", download_root=str(MODEL.parent), in_memory=False)
loaded_seconds = round(time.monotonic() - started, 3)
a = transcribe(model)
b = transcribe(model)
text_lower = a["text"].lower()
segments = a["segments"]
words = [word for segment in segments for word in segment["words"]]
assertions = {
    "exact_repeat_equal": a == b,
    "core_quote_terms_present": all(term in text_lower for term in ("acme signal", "synthetic buyers", "slow research", "customer data")),
    "segment_timecodes_present": bool(segments) and all(s["start"] <= s["end"] for s in segments),
    "word_timecodes_present": bool(words) and all(w["start"] <= w["end"] for w in words),
    "model_hash_matches_source_constant": sha256(MODEL) == "d3dd57d32accea0b295c96e26691aa14d8822fac7d9d27d5dc00b4ca2826dd03",
}
lineage = {
    "fixture_sha256": sha256(AUDIO),
    "model_sha256": sha256(MODEL),
    "model_name": "tiny.en",
    "source_commit": "04f449b8a437f1bbd3dba5c9f826aca972e7709a",
    "exact_transcript_output": a["text"],
    "segments": segments,
    "operator_status": "machine_candidate_requires_human_review",
}
summary = {
    "candidate": "Whisper",
    "version": whisper.__version__,
    "device": str(next(model.parameters()).device),
    "torch_version": torch.__version__,
    "model_load_seconds": loaded_seconds,
    "assertions": assertions,
    "pass": all(assertions.values()),
    "lineage": lineage,
    "consent_boundary": "No consent ledger or deletion workflow in library; caller must govern audio and derived transcript lifecycle.",
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary["pass"] else 2)
