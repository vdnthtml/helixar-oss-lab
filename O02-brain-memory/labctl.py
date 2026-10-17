#!/usr/bin/env python3
"""Execute lab commands with immutable-ish JSONL process/network receipts."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
PROCESS_LOG = ROOT / "process-log.jsonl"
NETWORK_LOG = ROOT / "network-fetch-log.jsonl"
COUNTER_FILE = ROOT / ".process-sequence"


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append(path: pathlib.Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def next_sequence() -> int:
    with COUNTER_FILE.open("a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        text = f.read().strip()
        sequence = int(text) + 1 if text else 5
        f.seek(0)
        f.truncate()
        f.write(str(sequence))
        f.flush()
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return sequence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("local", "network", "service"), required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        parser.error("command required after --")

    seq = next_sequence()
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.label)
    out_path = LOG_DIR / f"{seq:03d}-{safe_label}.stdout.log"
    err_path = LOG_DIR / f"{seq:03d}-{safe_label}.stderr.log"
    started = stamp()
    t0 = time.monotonic()
    with out_path.open("wb") as out, err_path.open("wb") as err:
        proc = subprocess.run(command, cwd=args.cwd, stdout=out, stderr=err, env=os.environ.copy())
    ended = stamp()
    record = {
        "sequence": seq,
        "kind": args.kind,
        "label": args.label,
        "cwd": str(pathlib.Path(args.cwd).resolve()),
        "argv": command,
        "shell": shlex.join(command),
        "started_at_utc": started,
        "ended_at_utc": ended,
        "duration_seconds": round(time.monotonic() - t0, 6),
        "exit_code": proc.returncode,
        "stdout_path": str(out_path),
        "stderr_path": str(err_path),
        "stdout_sha256": sha256(out_path),
        "stderr_sha256": sha256(err_path),
        "stdout_bytes": out_path.stat().st_size,
        "stderr_bytes": err_path.stat().st_size,
    }
    append(PROCESS_LOG, record)
    if args.kind == "network":
        append(NETWORK_LOG, {
            "sequence": seq,
            "label": args.label,
            "argv": command,
            "started_at_utc": started,
            "ended_at_utc": ended,
            "exit_code": proc.returncode,
            "response_evidence_stdout_sha256": record["stdout_sha256"],
            "response_evidence_stderr_sha256": record["stderr_sha256"],
        })
    print(json.dumps(record, indent=2))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
