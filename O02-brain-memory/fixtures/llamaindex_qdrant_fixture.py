#!/usr/bin/env python3
"""Offline LlamaIndex + embedded Qdrant deterministic retrieval/storage fixture."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import socket
from pathlib import Path
from typing import ClassVar, List

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "storage" / "llamaindex-qdrant-fixture"
EXPORT = ROOT / "exports" / "llamaindex-qdrant-export.json"
COLLECTION = "o02_llamaindex_qdrant"

from llama_index.core import StorageContext, VectorStoreIndex  # noqa: E402
from llama_index.core.base.embeddings.base import BaseEmbedding  # noqa: E402
from llama_index.core.schema import TextNode  # noqa: E402
from llama_index.core.vector_stores import MetadataFilters  # noqa: E402
from llama_index.vector_stores.qdrant import QdrantVectorStore  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402


class DeterministicEmbedding(BaseEmbedding):
    VOCAB: ClassVar[tuple[str, ...]] = ("alpha", "beta", "gamma", "launch", "finance", "policy", "approved", "revoked")

    @classmethod
    def class_name(cls) -> str:
        return "O02DeterministicEmbedding"

    def _vector(self, text: str) -> List[float]:
        lowered = text.lower()
        vector = [float(lowered.split().count(token)) for token in self.VOCAB]
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            digest = hashlib.sha256(lowered.encode()).digest()
            vector = [float((digest[i] % 17) + 1) for i in range(len(self.VOCAB))]
            norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector]

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._vector(text)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._vector(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._vector(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._vector(query)


def make_node(node_id: str, text: str, source_id: str, state: str) -> TextNode:
    return TextNode(
        id_=node_id,
        text=text,
        metadata={
            "source_id": source_id,
            "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "governance_state": state,
        },
    )


def projection(rows):
    return [
        {
            "id": row.node.node_id,
            "score": round(float(row.score or 0.0), 12),
            "text": row.node.get_content(),
            "source_id": row.node.metadata.get("source_id"),
            "governance_state": row.node.metadata.get("governance_state"),
        }
        for row in rows
    ]


def point_dict(point):
    if hasattr(point, "model_dump"):
        return point.model_dump(mode="json")
    if hasattr(point, "dict"):
        return point.dict()
    return json.loads(json.dumps(point, default=str))


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
    client = None
    try:
        embedder = DeterministicEmbedding(embed_batch_size=4)
        client = QdrantClient(path=str(STATE / "qdrant"))
        vector_store = QdrantVectorStore(collection_name=COLLECTION, client=client, enable_hybrid=False)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        proposed = make_node(
            "11111111-1111-4111-8111-111111111111",
            "alpha launch policy approved",
            "fixture://alpha-v1",
            "proposed",
        )
        beta = make_node(
            "22222222-2222-4222-8222-222222222222",
            "beta finance policy approved",
            "fixture://beta-v1",
            "approved",
        )
        delete_target = make_node(
            "33333333-3333-4333-8333-333333333333",
            "gamma temporary policy approved",
            "fixture://gamma-temp",
            "approved",
        )
        index = VectorStoreIndex(
            [proposed, beta, delete_target],
            storage_context=storage_context,
            embed_model=embedder,
        )

        approved_filters = MetadataFilters.from_dict({"governance_state": "approved"})
        before = index.as_retriever(similarity_top_k=10, filters=approved_filters).retrieve(
            "alpha launch policy approved"
        )
        assert proposed.node_id not in {row.node.node_id for row in before}

        governance_audit = [
            {"node_id": proposed.node_id, "event": "PROPOSE", "state": "proposed"},
        ]
        promoted = make_node(proposed.node_id, proposed.text, "fixture://alpha-v1", "approved")
        index.insert_nodes([promoted])
        governance_audit.append(
            {"node_id": proposed.node_id, "event": "APPROVE", "state": "approved", "actor": "synthetic-human.invalid"}
        )
        after_promotion = index.as_retriever(similarity_top_k=10, filters=approved_filters).retrieve(
            "alpha launch policy approved"
        )
        assert after_promotion and after_promotion[0].node.node_id == proposed.node_id
        assert after_promotion[0].node.metadata["source_id"] == "fixture://alpha-v1"

        index.delete_nodes([delete_target.node_id])
        points_after_delete, _ = client.scroll(COLLECTION, limit=100, with_payload=True, with_vectors=False)
        assert delete_target.node_id not in {str(point.id) for point in points_after_delete}
        governance_audit.append({"node_id": delete_target.node_id, "event": "DELETE", "state": "deleted"})

        revoked = make_node(proposed.node_id, proposed.text, "fixture://alpha-v1", "revoked")
        index.insert_nodes([revoked])
        governance_audit.append(
            {"node_id": proposed.node_id, "event": "REVOKE", "state": "revoked", "reason": "synthetic-test"}
        )
        after_revocation = index.as_retriever(similarity_top_k=10, filters=approved_filters).retrieve(
            "alpha launch policy approved"
        )
        assert proposed.node_id not in {row.node.node_id for row in after_revocation}

        repetitions = []
        for _ in range(5):
            rows = index.as_retriever(similarity_top_k=10, filters=approved_filters).retrieve(
                "beta finance policy approved"
            )
            repetitions.append(projection(rows))
        assert all(rows == repetitions[0] for rows in repetitions[1:])
        assert repetitions[0] and repetitions[0][0]["id"] == beta.node_id

        points, _ = client.scroll(COLLECTION, limit=100, with_payload=True, with_vectors=True)
        export_payload = {
            "candidate": "LlamaIndex+Qdrant embedded",
            "collection": COLLECTION,
            "governance_audit": governance_audit,
            "points": [point_dict(point) for point in points],
        }
        EXPORT.write_text(json.dumps(export_payload, indent=2, sort_keys=True, default=str) + "\n")
        exported = json.loads(EXPORT.read_text())
        exported_count = len(exported["points"])
        assert exported_count == 2

        client.close()
        client = None
        reopened = QdrantClient(path=str(STATE / "qdrant"))
        reloaded_points, _ = reopened.scroll(COLLECTION, limit=100, with_payload=True, with_vectors=True)
        reopened.close()
        assert len(reloaded_points) == exported_count

        assert not denied_egress
        summary = {
            "candidate": "LlamaIndex + Qdrant local mode",
            "status": "PASS",
            "public_api": [
                "VectorStoreIndex",
                "QdrantVectorStore",
                "as_retriever",
                "insert_nodes",
                "delete_nodes",
            ],
            "external_egress_attempts": denied_egress,
            "checks": {
                "source_lineage_round_trip": True,
                "promotion_filter": True,
                "revocation_excluded_from_current_retrieval": True,
                "external_audit_history_retained": len(governance_audit),
                "delete": True,
                "deterministic_retrieval_repetitions": len(repetitions),
                "export_reload": True,
                "persisted_points_after_reload": len(reloaded_points),
            },
            "storage_path": str(STATE / "qdrant"),
            "export_path": str(EXPORT),
            "approved_retrieval_order": repetitions[0],
            "proof_boundary": "Embedded qdrant-client persistence only; no Qdrant server, auth, replication, backup, or production operations were proven.",
            "governance_boundary": "Promotion/revocation audit is an external ledger; retrieval is filtered by explicit metadata and neither library is global truth.",
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    finally:
        socket.socket.connect = original_connect
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
