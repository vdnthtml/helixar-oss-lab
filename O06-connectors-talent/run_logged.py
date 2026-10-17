#!/usr/bin/env python3
"""Run one O06 lab command and append a sanitized process/fetch receipt."""
from __future__ import annotations

import csv
import datetime as dt
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

LAB = Path("/Users/vedantswami/Projects/helixar-oss-labs/O06-connectors-talent")
LEDGER = LAB / "logs" / "process-ledger.csv"
LOGS = LAB / "logs" / "commands"
LOGS.mkdir(parents=True, exist_ok=True)

if len(sys.argv) < 4:
    raise SystemExit("usage: run_logged.py KIND LABEL COMMAND [ARG ...]")
kind, label, *command = sys.argv[1:]
allowed = {"local_process", "public_network_fetch", "loopback_request"}
if kind not in allowed:
    raise SystemExit(f"kind must be one of {sorted(allowed)}")

started = dt.datetime.now(dt.timezone.utc).astimezone()
stamp = started.strftime("%Y%m%dT%H%M%S%z")
safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
log_path = LOGS / f"{stamp}-{safe_label}.log"
start = time.monotonic()
with log_path.open("wb") as output:
    proc = subprocess.run(command, cwd=os.environ.get("O06_CWD", str(LAB)), stdout=output, stderr=subprocess.STDOUT)
duration = round(time.monotonic() - start, 3)
finished = dt.datetime.now(dt.timezone.utc).astimezone()
exists = LEDGER.exists()
with LEDGER.open("a", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=["started_at", "finished_at", "kind", "label", "command", "cwd", "duration_s", "exit_code", "output_log"],
    )
    if not exists:
        writer.writeheader()
    writer.writerow(
        {
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "kind": kind,
            "label": label,
            "command": shlex.join(command),
            "cwd": os.environ.get("O06_CWD", str(LAB)),
            "duration_s": duration,
            "exit_code": proc.returncode,
            "output_log": str(log_path),
        }
    )
print(f"[{kind}] {label}: exit={proc.returncode} duration={duration}s log={log_path}")
if log_path.stat().st_size <= 20_000:
    print(log_path.read_text(encoding="utf-8", errors="replace"), end="")
else:
    print(f"output_size={log_path.stat().st_size} bytes (see log)")
raise SystemExit(proc.returncode)
