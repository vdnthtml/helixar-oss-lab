#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PROCESS_LOG = ROOT / "process-log.jsonl"
NETWORK_LOG = ROOT / "network-log.jsonl"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("process_id")
    parser.add_argument("kind", choices=("local", "network", "loopback"))
    parser.add_argument("cwd")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv and args.argv[0] == "--" else args.argv
    if not argv:
        parser.error("missing command after --")
    start_wall = dt.datetime.now(dt.timezone.utc)
    start = time.monotonic()
    run = subprocess.run(argv, cwd=args.cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    end = dt.datetime.now(dt.timezone.utc)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.process_id)
    stdout_path = LOG_DIR / f"{safe_id}.stdout"
    stderr_path = LOG_DIR / f"{safe_id}.stderr"
    stdout_path.write_bytes(run.stdout)
    stderr_path.write_bytes(run.stderr)
    record = {
        "process_id": args.process_id,
        "kind": args.kind,
        "network_declared": args.kind == "network",
        "loopback_declared": args.kind == "loopback",
        "started_at": start_wall.isoformat(),
        "ended_at": end.isoformat(),
        "duration_seconds": round(time.monotonic() - start, 3),
        "cwd": os.path.abspath(args.cwd),
        "argv": argv,
        "exit_code": run.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_sha256": digest(run.stdout),
        "stderr_sha256": digest(run.stderr),
        "stdout_bytes": len(run.stdout),
        "stderr_bytes": len(run.stderr),
    }
    with PROCESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    if args.kind == "network":
        with NETWORK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "fetch_id": args.process_id,
                "process_id": args.process_id,
                "purpose": "public network command",
                "url": "declared in argv",
                "started_at": start_wall.isoformat(),
                "ended_at": end.isoformat(),
                "duration_seconds": record["duration_seconds"],
                "exit_code": run.returncode,
            }, sort_keys=True) + "\n")
    sys.stdout.buffer.write(run.stdout)
    sys.stderr.buffer.write(run.stderr)
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
