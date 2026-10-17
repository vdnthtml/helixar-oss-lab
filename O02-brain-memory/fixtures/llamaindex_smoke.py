#!/usr/bin/env python3
"""Offline LlamaIndex core persistence and deterministic retrieval smoke fixture."""
from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE_ROOT = ROOT / "storage" / "llamaindex"
EXPORT_ROOT = ROOT / "exports"
STATE_ROOT.mkdir(parents=True, exist_ok=True)
EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
run_dir = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=STATE_ROOT))
persist_dir = run_dir / "index"

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode


class FixtureEmbedding(BaseEmbedding):
    @classmethod
    def class_name(cls) -> str:
        return "FixtureEmbedding"

    @staticmethod
    def _vector(text: str) -> list[float]:
        lowered = text.lower()
        return [1.0, float("alpha" in lowered), float("beta" in lowered), float("gamma" in lowered)]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._vector(text)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)


embed_model = FixtureEmbedding(model_name="fixture-keyword-v1")
source = RelatedNodeInfo(node_id="source.invalid/document-001")
nodes = [
    TextNode(
        id_="node-alpha",
        text="alpha memory",
        metadata={"source_uri": "https://source.invalid/document-001", "ordinal": 0, "state": "promoted"},
        relationships={NodeRelationship.SOURCE: source},
    ),
    TextNode(
        id_="node-beta",
        text="beta memory",
        metadata={"source_uri": "https://source.invalid/document-001", "ordinal": 1, "state": "promoted"},
        relationships={NodeRelationship.SOURCE: source},
    ),
]

storage = StorageContext.from_defaults()
index = VectorStoreIndex(nodes=nodes, storage_context=storage, embed_model=embed_model)
index.set_index_id("fixture-index-v1")

before_first = index.as_retriever(similarity_top_k=2).retrieve("beta")
before_second = index.as_retriever(similarity_top_k=2).retrieve("beta")
before_projection = [(item.node.node_id, item.node.ref_doc_id, round(float(item.score or 0.0), 12)) for item in before_first]
assert before_projection == [(item.node.node_id, item.node.ref_doc_id, round(float(item.score or 0.0), 12)) for item in before_second]
assert before_projection[0][0] == "node-beta"
assert before_first[0].node.ref_doc_id == "source.invalid/document-001"

storage.persist(persist_dir=str(persist_dir))
reloaded_storage = StorageContext.from_defaults(persist_dir=str(persist_dir))
reloaded = load_index_from_storage(reloaded_storage, index_id="fixture-index-v1", embed_model=embed_model)
after = reloaded.as_retriever(similarity_top_k=2).retrieve("beta")
after_projection = [(item.node.node_id, item.node.ref_doc_id, round(float(item.score or 0.0), 12)) for item in after]
assert after_projection == before_projection

export_rows = sorted(
    [
        {
            "node_id": node.node_id,
            "text": node.text,
            "source_uri": node.metadata["source_uri"],
            "ordinal": node.metadata["ordinal"],
            "state": node.metadata["state"],
            "ref_doc_id": node.ref_doc_id,
        }
        for node in nodes
    ],
    key=lambda row: row["node_id"],
)
export_blob = (json.dumps(export_rows, indent=2, sort_keys=True) + "\n").encode()
export_path = EXPORT_ROOT / "llamaindex-export.json"
export_path.write_bytes(export_blob)

summary = {
    "candidate": "LlamaIndex core",
    "run_dir": str(run_dir),
    "public_api_indexed_nodes": len(nodes),
    "source_lineage_retained": True,
    "deterministic_order_before_reload": before_projection,
    "persistence_reload_equal": True,
    "export_path": str(export_path),
    "export_sha256": hashlib.sha256(export_blob).hexdigest(),
    "hosted_provider_calls": 0,
    "external_business_writes": 0,
}
print(json.dumps(summary, indent=2, sort_keys=True))
