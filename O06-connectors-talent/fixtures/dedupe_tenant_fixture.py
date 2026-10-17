#!/usr/bin/env python3
"""Deterministic, synthetic tenant-partitioned identity clustering fixture."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import dedupe
import numpy as np

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "artifacts" / "dedupe-tenant-result.json"

records = {
    1: {"tenant": "acme.invalid", "email": "alice@acme.invalid", "name": "Alice Example"},
    2: {"tenant": "acme.invalid", "email": "alice+old@acme.invalid", "name": "Alice Example"},
    3: {"tenant": "acme.invalid", "email": "bob@acme.invalid", "name": "Bob Example"},
    4: {"tenant": "beta.invalid", "email": "alice@acme.invalid", "name": "Alice Example"},
    5: {"tenant": "beta.invalid", "email": "alice+import@beta.invalid", "name": "Alice Example"},
}
# Pre-scored candidate edges are intentionally generated only inside a tenant.
# This proves the required integration partition, not native dedupe tenant enforcement.
scores = {(1, 2): 0.96, (1, 3): 0.10, (2, 3): 0.10, (4, 5): 0.95}
by_tenant: dict[str, list[int]] = defaultdict(list)
for record_id, record in records.items():
    by_tenant[record["tenant"]].append(record_id)

clusters: list[dict[str, object]] = []
for tenant, ids in sorted(by_tenant.items()):
    edges = [((a, b), score) for (a, b), score in scores.items() if a in ids and b in ids]
    pairs = np.array(edges, dtype=[("pairs", "i8", 2), ("score", "f4")])
    for member_ids, confidence in dedupe.clustering.cluster(pairs, threshold=0.5):
        assert all(records[int(member)]["tenant"] == tenant for member in member_ids)
        clusters.append(
            {
                "tenant": tenant,
                "members": [int(member) for member in member_ids],
                "confidence": [round(float(value), 6) for value in confidence],
            }
        )

assert {tuple(item["members"]) for item in clusters} == {(1, 2), (4, 5)}
assert not any(1 in item["members"] and 4 in item["members"] for item in clusters)

# Export then deletion receipt for the synthetic identity state owned by this harness.
export_before_delete = [dict(id=record_id, **record) for record_id, record in sorted(records.items())]
del records[2]
assert 2 not in records
assert all(".invalid" in record["tenant"] for record in records.values())

result = {
    "status": "PASS",
    "library_version": getattr(dedupe, "__version__", "3.0.3-source"),
    "tenant_partition_enforced_by": "O06 fixture adapter; not a native dedupe authorization boundary",
    "clusters": clusters,
    "export_count_before_delete": len(export_before_delete),
    "deleted_record_id": 2,
    "remaining_record_ids": sorted(records),
    "cross_tenant_candidate_edges": 0,
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
