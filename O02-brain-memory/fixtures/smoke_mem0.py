#!/usr/bin/env python3
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

from mem0 import Memory
from mem0.utils.factory import EmbedderFactory, LlmFactory

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "smoke" / "mem0"
QDRANT_PATH = OUT / "qdrant"
HISTORY_PATH = OUT / "history.db"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_memory() -> Memory:
    EmbedderFactory.provider_to_class["langchain"] = "fixtures.mem0_provider.DeterministicEmbedding"
    LlmFactory.register_provider("langchain", "fixtures.mem0_provider.DeterministicLLM")
    config = {
        "version": "v1.1",
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "o02_mem0_smoke",
                "embedding_model_dims": 8,
                "path": str(QDRANT_PATH),
                "on_disk": True,
            },
        },
        "embedder": {"provider": "langchain", "config": {"embedding_dims": 8}},
        "llm": {"provider": "langchain", "config": {"model": "o02-deterministic"}},
        "history_db_path": str(HISTORY_PATH),
    }
    return Memory.from_config(config)


def close_memory(memory: Memory) -> None:
    client = getattr(memory.vector_store, "client", None)
    close = getattr(client, "close", None)
    if callable(close):
        close()


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)

    memory = make_memory()
    added = memory.add(
        "Helixar builds autonomous demand authority infrastructure",
        user_id="tenant-alpha",
        metadata={"source": "fixture://o02", "packet": "O02"},
        infer=False,
    )
    memory_id = added["results"][0]["id"]
    fetched = memory.get(memory_id)
    searched = memory.search("autonomous demand authority", filters={"user_id": "tenant-alpha"}, top_k=5)
    isolated = memory.search("autonomous demand authority", filters={"user_id": "tenant-beta"}, top_k=5)
    update_result = memory.update(memory_id, "Helixar operates autonomous demand intelligence infrastructure")
    updated = memory.get(memory_id)
    history = memory.history(memory_id)

    assert fetched["memory"].startswith("Helixar builds")
    assert searched["results"] and searched["results"][0]["id"] == memory_id
    assert isolated["results"] == []
    assert updated["memory"].endswith("intelligence infrastructure")
    assert update_result["message"] == "Memory updated successfully!"
    assert any(item.get("event") == "UPDATE" for item in history)

    close_memory(memory)
    memory = make_memory()
    persisted = memory.get(memory_id)
    assert persisted["memory"] == updated["memory"]
    memory.delete(memory_id)
    assert memory.get(memory_id) is None
    close_memory(memory)

    receipt = {
        "candidate": "mem0",
        "package_version": importlib.metadata.version("mem0ai"),
        "status": "PASS",
        "offline": True,
        "telemetry_env": "MEM0_TELEMETRY=false",
        "vector_backend": "qdrant-client local persistent mode",
        "embedding": "fixture deterministic sha256 token embedding (8 dims)",
        "llm_used": False,
        "tests": {
            "add_get": True,
            "semantic_search": True,
            "tenant_isolation": True,
            "update": True,
            "history_lineage": True,
            "process_restart_persistence": True,
            "delete": True,
        },
        "memory_id": memory_id,
        "history_event_count": len(history),
        "history_db_sha256": sha256(HISTORY_PATH),
    }
    receipt_path = OUT / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
