#!/usr/bin/env python3
"""O03 disposable lab command runner with process/network receipts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROCESS_LOG = ROOT / "process-log.jsonl"
NETWORK_LOG = ROOT / "network-log.jsonl"


def append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("--network-url", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("command required after --")
    started = dt.datetime.now(dt.timezone.utc)
    t0 = time.monotonic()
    proc = subprocess.run(
        command,
        cwd=args.cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=args.timeout,
        env=os.environ.copy(),
    )
    ended = dt.datetime.now(dt.timezone.utc)
    duration = round(time.monotonic() - t0, 3)
    record = {
        "process_id": args.id,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_seconds": duration,
        "cwd": str(Path(args.cwd).resolve()),
        "argv": command,
        "exit_code": proc.returncode,
        "output": proc.stdout[-12000:],
        "network_declared": bool(args.network_url),
    }
    append(PROCESS_LOG, record)
    for url in args.network_url:
        append(
            NETWORK_LOG,
            {
                "fetch_id": f"{args.id}:{url}",
                "process_id": args.id,
                "url": url,
                "started_at": started.isoformat(),
                "ended_at": ended.isoformat(),
                "duration_seconds": duration,
                "exit_code": proc.returncode,
                "purpose": "public OSS source or dependency fetch",
            },
        )
    sys.stdout.write(proc.stdout)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
