#!/usr/bin/env python3
"""Run a local O01 lab command and append an auditable process/network log."""
from __future__ import annotations
import argparse, datetime as dt, json, os, shlex, subprocess, sys, time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--candidate", required=True)
p.add_argument("--kind", choices=["local", "network"], required=True)
p.add_argument("--url", action="append", default=[])
p.add_argument("--cwd", default=os.getcwd())
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
if a.command and a.command[0] == "--":
    a.command = a.command[1:]
if not a.command:
    raise SystemExit("command required")
root = Path(__file__).resolve().parent
log_dir = root / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
start = dt.datetime.now(dt.timezone.utc)
t0 = time.monotonic()
try:
    proc = subprocess.run(a.command, cwd=a.cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout
    exit_code = proc.returncode
except OSError as exc:
    output = f"{type(exc).__name__}: {exc}\n"
    exit_code = 127
end = dt.datetime.now(dt.timezone.utc)
record = {
    "candidate": a.candidate,
    "kind": a.kind,
    "urls": a.url,
    "cwd": a.cwd,
    "argv": a.command,
    "command": shlex.join(a.command),
    "started_at_utc": start.isoformat(),
    "ended_at_utc": end.isoformat(),
    "duration_seconds": round(time.monotonic() - t0, 3),
    "exit_code": exit_code,
}
with (log_dir / "process-network.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(record, sort_keys=True) + "\n")
safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in a.candidate)
with (log_dir / f"{safe}.log").open("a", encoding="utf-8") as f:
    f.write(f"\n=== {record['started_at_utc']} {record['command']} ===\n")
    f.write(output)
print(output, end="")
raise SystemExit(exit_code)
