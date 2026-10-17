#!/usr/bin/env python3
"""Deterministic, offline Mem0 + embedded-Qdrant lifecycle smoke fixture."""

from __future__ import annotations

import json
import os
import shutil
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
STATE = LAB / "state" / "mem0-smoke"
FIXTURES = LAB / "fixtures"
sys.path.insert(0, str(FIXTURES))
os.environ["MEM0_TELEMETRY"] = "false"
os.environ["MEM0_DIR"] = str(STATE / "mem0-home")

_original_connect = socket.socket.connect


def _loopback_only_connect(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6):
        host = address[0]
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise RuntimeError(f"external network blocked by O02 fixture: {host}")
    return _original_connect(sock, address)


socket.socket.connect = _loopback_only_connect

from mem0 import Memory  # noqa: E402
from mem0.configs.llms.base import BaseLlmConfig  # noqa: E402
from mem0.utils.factory import EmbedderFactory, LlmFactory  # noqa: E402

EmbedderFactory.provider_to_class["langchain"] = (
    "o02_test_providers.DeterministicEmbedder"
)
LlmFactory.provider_to_class["langchain"] = (
    "o02_test_providers.DeterministicLLM",
    BaseLlmConfig,
)


def config() -> dict:
    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "o02_mem0_smoke",
                "embedding_model_dims": 8,
                "path": str(STATE / "qdrant"),
                "on_disk": True,
            },
        },
        "embedder": {
            "provider": "langchain",
            "config": {"model": "o02-deterministic", "embedding_dims": 8},
        },
        "llm": {
            "provider": "langchain",
            "config": {"model": "o02-no-inference"},
        },
        "history_db_path": str(STATE / "history.sqlite"),
        "version": "v1.1",
    }


def close_memory(memory: Memory) -> None:
    memory.db.connection.close()
    close = getattr(memory.vector_store.client, "close", None)
    if close:
        close()


def main() -> None:
    shutil.rmtree(STATE, ignore_errors=True)
    STATE.mkdir(parents=True)
    memory = Memory.from_config(config())
    user_id = "o02-user"

    seed = memory.add(
        "Helixar deploys governed memory adapters.",
        user_id=user_id,
        metadata={"source_id": "source-001", "governance_state": "proposed"},
        infer=False,
    )["results"][0]
    seed_id = seed["id"]
    assert memory.get(seed_id)["metadata"]["source_id"] == "source-001"

    memory.update(seed_id, metadata={"governance_state": "approved"})
    approved = memory.search(
        "governed memory adapters",
        filters={"user_id": user_id, "governance_state": "approved"},
        top_k=10,
        threshold=0.0,
    )["results"]
    assert seed_id in {item["id"] for item in approved}

    concurrent_texts = [f"Concurrent governed fact {index:02d}" for index in range(8)]

    def add_one(text: str) -> str:
        return memory.add(
            text,
            user_id=user_id,
            metadata={"source_id": f"batch-{text[-2:]}", "governance_state": "approved"},
            infer=False,
        )["results"][0]["id"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        concurrent_ids = list(executor.map(add_one, concurrent_texts))
    assert len(set(concurrent_ids)) == len(concurrent_texts)

    ranked_ids = []
    for _ in range(3):
        ranked_ids.append(
            [
                item["id"]
                for item in memory.search(
                    "Concurrent governed fact 03",
                    filters={"user_id": user_id, "governance_state": "approved"},
                    top_k=5,
                    threshold=0.0,
                )["results"]
            ]
        )
    assert ranked_ids[0] == ranked_ids[1] == ranked_ids[2]

    memory.update(seed_id, metadata={"governance_state": "revoked"})
    post_revoke = memory.search(
        "governed memory adapters",
        filters={"user_id": user_id, "governance_state": "approved"},
        top_k=20,
        threshold=0.0,
    )["results"]
    assert seed_id not in {item["id"] for item in post_revoke}
    seed_history = memory.history(seed_id)
    assert [entry["event"] for entry in seed_history].count("UPDATE") >= 2

    deleted_id = concurrent_ids[-1]
    memory.delete(deleted_id)
    assert memory.get(deleted_id) is None
    assert any(entry["event"] == "DELETE" for entry in memory.history(deleted_id))

    export_before = sorted(
        (
            item["id"],
            item["memory"],
            (item.get("metadata") or {}).get("source_id"),
        )
        for item in memory.get_all(filters={"user_id": user_id}, top_k=100)["results"]
    )
    export_path = STATE / "export.json"
    export_path.write_text(json.dumps(export_before, indent=2), encoding="utf-8")
    export_hash_before = __import__("hashlib").sha256(export_path.read_bytes()).hexdigest()

    close_memory(memory)
    del memory

    reopened = Memory.from_config(config())
    export_after = sorted(
        (
            item["id"],
            item["memory"],
            (item.get("metadata") or {}).get("source_id"),
        )
        for item in reopened.get_all(filters={"user_id": user_id}, top_k=100)["results"]
    )
    assert export_before == export_after
    close_memory(reopened)

    result = {
        "candidate": "Mem0",
        "status": "PASS",
        "network_policy": "external-blocked; embedded storage only",
        "telemetry": os.environ["MEM0_TELEMETRY"],
        "checks": {
            "write_read": True,
            "source_lineage": True,
            "deterministic_retrieval": True,
            "concurrent_writes": len(concurrent_ids),
            "promotion_filter": True,
            "revocation_filter": True,
            "history_after_update_delete": True,
            "export_reopen_equal": True,
            "deleted_id_absent": True,
        },
        "record_count_after_delete": len(export_after),
        "export_sha256": export_hash_before,
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
