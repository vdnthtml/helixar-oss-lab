#!/usr/bin/env python3
"""Remove Nango CLI global state created during this O06 run without reading its value."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

state = Path.home() / "Library" / "Preferences" / "nango-nodejs" / "config.json"
result: dict[str, object]
if state.exists():
    stat = state.stat()
    digest = hashlib.sha256(state.read_bytes()).hexdigest()
    if stat.st_birthtime < 1784051050 or stat.st_size != 55:
        raise RuntimeError("refusing to delete unexpected Nango CLI state")
    state.unlink()
    parent_removed = False
    try:
        state.parent.rmdir()
        parent_removed = True
    except OSError:
        pass
    result = {
        "status": "PASS",
        "path": str(state),
        "bytesRemoved": stat.st_size,
        "sha256": digest,
        "parentRemovedIfEmpty": parent_removed,
    }
else:
    result = {"status": "PASS", "path": str(state), "bytesRemoved": 0, "alreadyAbsent": True}
print(json.dumps(result, sort_keys=True))
