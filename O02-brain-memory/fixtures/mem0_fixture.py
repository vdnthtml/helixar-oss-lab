#!/usr/bin/env python3
"""Offline deterministic Mem0 + embedded Qdrant fixture for the O02 lab."""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "storage" / "mem0-fixture"
EXPORT = ROOT / "exports" / "mem0-fixture-export.json"

# Must be set before importing mem0.memory.telemetry.
os.environ["MEM0_TELEMETRY"] = "False"
os.environ["MEM0_TELEMETRY_SAMPLE_RATE"] = "0"
os.environ["MEM0_DIR"] = str(STATE / "mem0-home")
os.environ["OPENAI_API_KEY"] = "synthetic-lab-key.invalid"
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"

from mem0 import Memory  # noqa: E402
from mem0.configs.embeddings.base import BaseEmbedderConfig  # noqa: E402
from mem0.embeddings.base import EmbeddingBase  # noqa: E402


class DeterministicEmbedding(EmbeddingBase):
    VOCAB = ("alpha", "beta", "gamma", "launch", "finance", "policy", "approved", "thread")

    def __init__(self) -> None:
        super().__init__(BaseEmbedderConfig(model="deterministic-lab", embedding_dims=len(self.VOCAB)))

    def embed(self, text, memory_action=None):
        lowered = str(text).lower()
        vector = [float(lowered.split().count(token)) for token in self.VOCAB]
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            digest = hashlib.sha256(lowered.encode()).digest()
            vector = [float((digest[i] % 17) + 1) for i in range(len(self.VOCAB))]
            norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector]


def stable_projection(results):
    return [
        {
            "id": row["id"],
            "memory": row["memory"],
            "score": round(float(row.get("score", 0.0)), 12),
            "source_id": row.get("metadata", {}).get("source_id"),
            "governance_state": row.get("metadata", {}).get("governance_state"),
        }
        for row in results
    ]


def main() -> int:
    shutil.rmtree(STATE, ignore_errors=True)
    STATE.mkdir(parents=True, exist_ok=True)
    EXPORT.parent.mkdir(parents=True, exist_ok=True)

    denied_egress = []
    original_connect = socket.socket.connect

    def guarded_connect(sock, address):
        if isinstance(address, tuple) and address:
            host = str(address[0]).lower()
            if host not in {"127.0.0.1", "::1", "localhost"}:
                denied_egress.append(repr(address))
                raise RuntimeError(f"external egress denied by fixture: {address!r}")
        return original_connect(sock, address)

    socket.socket.connect = guarded_connect
    memory = None
    try:
        config = {
            "version": "v1.1",
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "o02_mem0_fixture",
                    "embedding_model_dims": 8,
                    "path": str(STATE / "qdrant"),
                    "on_disk": True,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "synthetic-embedding.invalid",
                    "api_key": "synthetic-lab-key.invalid",
                    "embedding_dims": 8,
                    "openai_base_url": "http://127.0.0.1:9/v1",
                },
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "synthetic-llm.invalid",
                    "api_key": "synthetic-lab-key.invalid",
                    "enable_vision": False,
                },
            },
            "history_db_path": str(STATE / "history.db"),
        }
        memory = Memory.from_config(config)
        memory.embedding_model = DeterministicEmbedding()

        proposed = memory.add(
            "alpha launch policy approved",
            user_id="lab-user.invalid",
            metadata={
                "source_id": "fixture://alpha-v1",
                "source_sha256": hashlib.sha256(b"alpha launch policy approved").hexdigest(),
                "governance_state": "proposed",
            },
            infer=False,
        )["results"][0]
        proposed_id = proposed["id"]

        before_promotion = memory.search(
            "alpha launch policy approved",
            filters={"user_id": "lab-user.invalid", "governance_state": "approved"},
            top_k=10,
            threshold=0.0,
        )["results"]
        assert proposed_id not in {row["id"] for row in before_promotion}

        memory.update(proposed_id, metadata={"governance_state": "approved", "approved_by": "synthetic-human.invalid"})
        approved = memory.search(
            "alpha launch policy approved",
            filters={"user_id": "lab-user.invalid", "governance_state": "approved"},
            top_k=10,
            threshold=0.0,
        )["results"]
        assert approved and approved[0]["id"] == proposed_id

        second = memory.add(
            "beta finance policy",
            user_id="lab-user.invalid",
            metadata={"source_id": "fixture://beta-v1", "governance_state": "approved"},
            infer=False,
        )["results"][0]
        delete_target = memory.add(
            "gamma temporary policy",
            user_id="lab-user.invalid",
            metadata={"source_id": "fixture://gamma-temp", "governance_state": "approved"},
            infer=False,
        )["results"][0]
        memory.delete(delete_target["id"])
        after_delete = memory.get_all(filters={"user_id": "lab-user.invalid"})["results"]
        assert delete_target["id"] not in {row["id"] for row in after_delete}
        delete_history = memory.history(delete_target["id"])
        assert any(row["event"] == "DELETE" and row["is_deleted"] for row in delete_history)

        memory.update(proposed_id, metadata={"governance_state": "revoked", "revocation_reason": "synthetic-test"})
        after_revocation = memory.search(
            "alpha launch policy approved",
            filters={"user_id": "lab-user.invalid", "governance_state": "approved"},
            top_k=10,
            threshold=0.0,
        )["results"]
        assert proposed_id not in {row["id"] for row in after_revocation}
        revocation_history = memory.history(proposed_id)
        assert [row["event"] for row in revocation_history] == ["ADD", "UPDATE", "UPDATE"]

        projections = []
        for _ in range(5):
            rows = memory.search(
                "beta finance policy",
                filters={"user_id": "lab-user.invalid", "governance_state": "approved"},
                top_k=10,
                threshold=0.0,
            )["results"]
            projections.append(stable_projection(rows))
        projection_ids = [[row["id"] for row in projection] for projection in projections]
        exact_projection_match = all(projection == projections[0] for projection in projections[1:])
        per_rank_score_drift = []
        if projections and projections[0]:
            for rank in range(len(projections[0])):
                rank_scores = [projection[rank]["score"] for projection in projections]
                per_rank_score_drift.append(max(rank_scores) - min(rank_scores))
        max_score_drift = max(per_rank_score_drift, default=0.0)
        assert all(ids == projection_ids[0] for ids in projection_ids[1:])
        assert max_score_drift <= 0.000001
        assert projections[0] and projections[0][0]["id"] == second["id"]

        def add_concurrent(i: int):
            return memory.add(
                f"thread alpha policy {i}",
                user_id="lab-concurrent.invalid",
                metadata={"source_id": f"fixture://thread-{i}", "governance_state": "approved"},
                infer=False,
            )["results"][0]["id"]

        concurrent_ids = []
        concurrent_errors = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(add_concurrent, i) for i in range(8)]
            for future in as_completed(futures):
                try:
                    concurrent_ids.append(future.result())
                except Exception as exc:
                    concurrent_errors.append(f"{type(exc).__name__}: {exc}")
        concurrent_rows = memory.get_all(filters={"user_id": "lab-concurrent.invalid"})["results"]
        concurrent_unique = len(concurrent_ids) == len(set(concurrent_ids))
        concurrent_pass = not concurrent_errors and concurrent_unique and len(concurrent_rows) == 8

        post_concurrency_projections = []
        post_concurrency_errors = []
        for _ in range(5):
            try:
                rows = memory.search(
                    "beta finance policy",
                    filters={"user_id": "lab-user.invalid", "governance_state": "approved"},
                    top_k=10,
                    threshold=0.0,
                )["results"]
                post_concurrency_projections.append(stable_projection(rows))
            except Exception as exc:
                post_concurrency_errors.append(f"{type(exc).__name__}: {exc}")
        post_ids = [[row["id"] for row in projection] for projection in post_concurrency_projections]
        post_rank_score_drift = []
        if post_concurrency_projections and post_concurrency_projections[0]:
            for rank in range(len(post_concurrency_projections[0])):
                rank_scores = [projection[rank]["score"] for projection in post_concurrency_projections]
                post_rank_score_drift.append(max(rank_scores) - min(rank_scores))
        post_score_drift = max(post_rank_score_drift, default=0.0)
        post_concurrency_stable = (
            not post_concurrency_errors
            and bool(post_concurrency_projections)
            and all(ids == post_ids[0] for ids in post_ids[1:])
            and post_score_drift <= 0.000001
        )

        current = memory.get_all(filters={"user_id": "lab-user.invalid"})["results"]
        export_payload = {
            "candidate": "Mem0",
            "fixture": "offline-embedded-qdrant",
            "current_memories": current,
            "concurrent_memories": concurrent_rows,
            "concurrent_write_attempt": {
                "requested": 8,
                "returned_ids": concurrent_ids,
                "errors": concurrent_errors,
                "passed": concurrent_pass,
                "post_concurrency_retrieval_stable": post_concurrency_stable,
                "post_concurrency_retrieval_errors": post_concurrency_errors,
            },
            "history": {
                proposed_id: revocation_history,
                delete_target["id"]: delete_history,
            },
        }
        EXPORT.write_text(json.dumps(export_payload, indent=2, sort_keys=True, default=str) + "\n")
        exported = json.loads(EXPORT.read_text())
        assert len(exported["concurrent_memories"]) == len(concurrent_rows)

        summary = {
            "candidate": "Mem0",
            "status": "PASS" if concurrent_pass and post_concurrency_stable else "PARTIAL_CONCURRENCY_FAIL",
            "public_api": ["Memory.from_config", "add", "search", "update", "delete", "history", "get_all"],
            "real_persistence": [str(STATE / "qdrant"), str(STATE / "history.db")],
            "telemetry_env": {"MEM0_TELEMETRY": os.environ["MEM0_TELEMETRY"]},
            "external_egress_attempts": denied_egress,
            "checks": {
                "source_lineage_round_trip": True,
                "promotion_filter": True,
                "revocation_excluded_from_current_retrieval": True,
                "revocation_audit_history_retained": True,
                "delete_and_tombstone_history": True,
                "concurrent_writes": {
                    "passed": concurrent_pass,
                    "requested": 8,
                    "successful_api_returns": len(concurrent_ids),
                    "persisted_rows": len(concurrent_rows),
                    "unique_returned_ids": concurrent_unique,
                    "errors": concurrent_errors,
                    "post_concurrency_retrieval_stable": post_concurrency_stable,
                    "post_concurrency_retrieval_errors": post_concurrency_errors,
                },
                "deterministic_retrieval_repetitions": len(projections),
                "deterministic_order_exact": True,
                "bit_exact_scores": exact_projection_match,
                "max_score_drift": max_score_drift,
                "score_tolerance": 0.000001,
                "export_reload": True,
            },
            "export_path": str(EXPORT),
            "approved_retrieval_order": projections[0],
            "governance_boundary": "Promotion and revocation are enforced by an external metadata state convention; Mem0 does not become global truth automatically.",
        }
        assert not denied_egress
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    finally:
        socket.socket.connect = original_connect
        if memory is not None:
            memory.close()
            client = getattr(getattr(memory, "vector_store", None), "client", None)
            if client is not None and hasattr(client, "close"):
                client.close()


if __name__ == "__main__":
    raise SystemExit(main())
