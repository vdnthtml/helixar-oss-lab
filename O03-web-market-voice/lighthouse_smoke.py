#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 18731
FIXTURE_DIR = ROOT / "fixtures" / "web"
OUT = ROOT / "artifacts" / "lighthouse"
OUT.mkdir(parents=True, exist_ok=True)
SERVICE_LOG = ROOT / "service-log.jsonl"
CLI = ROOT / "repos" / "lighthouse" / "cli" / "index.js"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def append(record: dict) -> None:
    with SERVICE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def wait_ready() -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("fixture server did not bind to loopback")


def main() -> None:
    server_argv = [
        "python3", "-m", "http.server", str(PORT),
        "--bind", "127.0.0.1", "--directory", str(FIXTURE_DIR),
    ]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    server = subprocess.Popen(server_argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    append({"service_id": "synthetic-web", "event": "started", "at": started, "pid": server.pid, "argv": server_argv, "bind": "127.0.0.1", "port": PORT})
    try:
        wait_ready()
        result_path = OUT / "report.json"
        argv = [
            "node", str(CLI), f"http://127.0.0.1:{PORT}/index.html",
            "--output=json", f"--output-path={result_path}",
            "--only-categories=accessibility,best-practices,seo",
            f"--chrome-path={CHROME}",
            "--chrome-flags=--headless --disable-background-networking --disable-component-update --disable-default-apps --disable-sync --metrics-recording-only --no-first-run",
            "--no-enable-error-reporting", "--quiet",
        ]
        t0 = time.monotonic()
        run = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240)
        elapsed = round(time.monotonic() - t0, 3)
        append({"service_id": "lighthouse-cli", "event": "completed", "at": dt.datetime.now(dt.timezone.utc).isoformat(), "argv": argv, "exit_code": run.returncode, "duration_seconds": elapsed, "output": run.stdout[-8000:]})
        if run.returncode != 0:
            raise SystemExit(run.returncode)
        report = json.loads(result_path.read_text(encoding="utf-8"))
        assertions = {
            "requested_url_loopback": report.get("requestedUrl") == f"http://127.0.0.1:{PORT}/index.html",
            "final_url_loopback": str(report.get("finalDisplayedUrl", report.get("finalUrl", ""))).startswith(f"http://127.0.0.1:{PORT}/"),
            "three_categories_present": all(k in report.get("categories", {}) for k in ("accessibility", "best-practices", "seo")),
            "audits_nonempty": len(report.get("audits", {})) > 0,
        }
        summary = {
            "candidate": "Lighthouse",
            "version": report.get("lighthouseVersion"),
            "fetch_time": report.get("fetchTime"),
            "duration_seconds": elapsed,
            "assertions": assertions,
            "category_scores": {k: v.get("score") for k, v in report.get("categories", {}).items()},
            "pass": all(assertions.values()),
            "determinism_boundary": "Structural assertions only; performance/browser metrics are variable by project documentation.",
        }
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        if not summary["pass"]:
            raise SystemExit(2)
    finally:
        server.terminate()
        try:
            output, _ = server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            output, _ = server.communicate()
        append({"service_id": "synthetic-web", "event": "stopped", "at": dt.datetime.now(dt.timezone.utc).isoformat(), "pid": server.pid, "exit_code": server.returncode, "output": (output or "")[-4000:]})


if __name__ == "__main__":
    main()
