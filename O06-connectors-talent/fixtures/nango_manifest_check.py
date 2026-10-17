#!/usr/bin/env python3
"""Validate the compile-only Nango connector manifest without credentials."""
from __future__ import annotations

import json
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
PROJECT = LAB / "fixtures" / "nango-smoke"
manifest_path = PROJECT / ".nango" / "nango.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
mock = next(item for item in manifest if item["providerConfigKey"] == "mock-api")
action = next(item for item in mock["actions"] if item["name"] == "upsertSyntheticContact")
assert action["endpoint"] == {"method": "POST", "path": "/o06/contacts", "group": "O06 Synthetic"}
assert action["version"] == "1.0.0"
assert action["input"].startswith("ActionInput_")

source = (PROJECT / "mock-api" / "actions" / "upsertSyntheticContact.ts").read_text(encoding="utf-8")
build = (PROJECT / "build" / "mock-api_actions_upsertSyntheticContact.cjs").read_text(encoding="utf-8")
for forbidden in ("access_token", "refresh_token", "client_secret", "api_key", "Bearer "):
    assert forbidden not in source
    assert forbidden not in build
assert ".invalid" in source

result = {
    "status": "PASS",
    "providerConfigKey": mock["providerConfigKey"],
    "action": action["name"],
    "endpoint": action["endpoint"],
    "compiledArtifact": str((PROJECT / "build" / "mock-api_actions_upsertSyntheticContact.cjs").relative_to(LAB)),
    "credentialValuesUsed": 0,
    "realConnectorCalls": 0,
    "tokenIsolation": "NOT_PROVEN: compile fixture contained no tokens; Nango server/keystore was not started",
}
(LAB / "artifacts" / "nango-connector-smoke.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
