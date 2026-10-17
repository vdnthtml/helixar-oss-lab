#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
names = ["mem0", "llamaindex", "unstructured", "graphiti"]
clean_env = dict(os.environ)
for key in ["PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__"]:
    clean_env.pop(key, None)
clean_env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
results = []
for name in names:
    python = ROOT / "envs" / name / "bin" / "python"
    completed = subprocess.run(
        [str(python), "-m", "pip", "check"],
        cwd=ROOT,
        env=clean_env,
        text=True,
        capture_output=True,
        check=False,
    )
    cfg = (ROOT / "envs" / name / "pyvenv.cfg").read_text(encoding="utf-8")
    results.append({
        "environment": name,
        "python": str(python),
        "include_system_site_packages_false": "include-system-site-packages = false" in cfg,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "pass": completed.returncode == 0,
    })
output = {
    "sanitized_environment_keys": ["PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__"],
    "all_pass": all(row["pass"] for row in results),
    "results": results,
}
path = ROOT / "artifacts" / "candidate-environment-isolation.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(output, indent=2, sort_keys=True))
raise SystemExit(0 if output["all_pass"] else 1)
