#!/usr/bin/env python3
"""Offline Graphiti EntityNode CRUD/lineage fixture using the deprecated Kuzu adapter."""
from __future__ import annotations

import asyncio
import gc
import hashlib
import json
import os
import shutil
import socket
from pathlib import Path

os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "false"
os.environ["DO_NOT_TRACK"] = "1"

from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.errors import NodeNotFoundError
from graphiti_core.nodes import EntityNode
from graphiti_core.telemetry.telemetry import is_telemetry_enabled

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "storage" / "graphiti-kuzu-fixture"
EXPORT = ROOT / "exports" / "graphiti-kuzu-export.json"
UUID = "44444444-4444-4444-8444-444444444444"


async def run() -> dict:
    shutil.rmtree(STATE, ignore_errors=True)
    STATE.mkdir(parents=True, exist_ok=True)
    EXPORT.parent.mkdir(parents=True, exist_ok=True)

    denied_egress: list[str] = []
    original_connect = socket.socket.connect

    def guarded_connect(sock, address):
        if isinstance(address, tuple) and address:
            host = str(address[0]).lower()
            if host not in {"127.0.0.1", "::1", "localhost"}:
                denied_egress.append(repr(address))
                raise RuntimeError(f"external egress denied by fixture: {address!r}")
        return original_connect(sock, address)

    socket.socket.connect = guarded_connect
    driver = None
    try:
        assert not is_telemetry_enabled()
        driver = KuzuDriver(db=str(STATE / "graph.kuzu"))
        source_text = "alpha launch policy approved"
        node = EntityNode(
            uuid=UUID,
            name="Alpha launch policy",
            group_id="tenant-a.invalid",
            labels=["Policy"],
            name_embedding=[1.0, 0.0, 0.0, 0.0],
            summary=source_text,
            attributes={
                "source_id": "fixture://alpha-v1",
                "source_sha256": hashlib.sha256(source_text.encode()).hexdigest(),
                "governance_state": "approved",
            },
        )
        await node.save(driver)
        loaded = await EntityNode.get_by_uuid(driver, UUID)
        assert loaded.group_id == "tenant-a.invalid"
        assert loaded.attributes["source_id"] == "fixture://alpha-v1"
        assert loaded.attributes["governance_state"] == "approved"

        loaded.attributes["governance_state"] = "revoked"
        loaded.attributes["revocation_reason"] = "synthetic-test"
        await loaded.save(driver)
        revoked = await EntityNode.get_by_uuid(driver, UUID)
        assert revoked.attributes["governance_state"] == "revoked"

        other_groups = await EntityNode.get_by_group_ids(driver, ["tenant-b.invalid"])
        assert all(item.uuid != UUID for item in other_groups)

        export_payload = {
            "candidate": "Graphiti",
            "backend": "Kuzu local adapter (deprecated upstream)",
            "node": revoked.model_dump(mode="json"),
        }
        EXPORT.write_text(json.dumps(export_payload, indent=2, sort_keys=True) + "\n")
        assert json.loads(EXPORT.read_text())["node"]["attributes"]["source_id"] == "fixture://alpha-v1"

        await revoked.delete(driver)
        deleted = False
        try:
            await EntityNode.get_by_uuid(driver, UUID)
        except NodeNotFoundError:
            deleted = True
        assert deleted
        assert not denied_egress
        return {
            "candidate": "Graphiti",
            "status": "PASS_BOUNDED_CRUD_ONLY",
            "backend": "Kuzu local adapter",
            "telemetry_enabled": is_telemetry_enabled(),
            "external_egress_attempts": denied_egress,
            "checks": {
                "entity_save_get": True,
                "source_lineage_round_trip": True,
                "governance_metadata_update": True,
                "cross_group_query_exclusion": True,
                "json_export_reload": True,
                "hard_delete": True,
            },
            "export_path": str(EXPORT),
            "proof_boundary": "Graph storage CRUD only; Kuzu adapter is deprecated and no episode extraction, temporal-edge search, Neo4j/FalkorDB, LLM, concurrency, backup, or production operations were proven.",
        }
    finally:
        socket.socket.connect = original_connect
        if driver is not None:
            await driver.close()
        gc.collect()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(run()), indent=2, sort_keys=True))
