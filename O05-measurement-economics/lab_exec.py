#!/usr/bin/env python3
"""Run one lab command and append a durable, sanitized activity record."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
ACTIVITY = LOG_DIR / "activity.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--kind", choices=["local", "network"], required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        parser.error("command is required")

    started = dt.datetime.now(dt.timezone.utc).astimezone()
    start = time.monotonic()
    log_path = LOG_DIR / f"{args.id}.log"
    env = os.environ.copy()
    env.update({"GIT_TERMINAL_PROMPT": "0", "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
    result: dict[str, object]
    try:
        proc = subprocess.run(
            args.command,
            cwd=args.cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.timeout,
            check=False,
        )
        output = proc.stdout
        exit_code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        timed_output = exc.stdout or ""
        if isinstance(timed_output, bytes):
            timed_output = timed_output.decode("utf-8", errors="replace")
        output = timed_output + "\nTIMEOUT\n"
        exit_code = 124
        timed_out = True

    log_path.write_text(output, encoding="utf-8")
    finished = dt.datetime.now(dt.timezone.utc).astimezone()
    result = {
        "id": args.id,
        "kind": args.kind,
        "url": args.url or None,
        "command": args.command,
        "cwd": str(pathlib.Path(args.cwd).resolve()),
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": round(time.monotonic() - start, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "output_log": str(log_path),
    }
    with ACTIVITY.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, sort_keys=True) + "\n")
    sys.stdout.write(output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
