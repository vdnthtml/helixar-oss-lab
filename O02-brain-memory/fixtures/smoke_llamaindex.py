#!/usr/bin/env python3
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

from llama_index.core import Document, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.embeddings import MockEmbedding

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "smoke" / "llamaindex"
PERSIST = OUT / "storage"


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    embed = MockEmbedding(embed_dim=8)
    documents = [
        Document(text="Helixar maps emerging demand before markets become crowded.", id_="doc-demand", metadata={"source": "fixture://demand", "tenant": "alpha"}),
        Document(text="Backup receipts preserve lineage and deterministic restore evidence.", id_="doc-backup", metadata={"source": "fixture://backup", "tenant": "alpha"}),
    ]
    index = VectorStoreIndex.from_documents(documents, embed_model=embed)
    before = index.as_retriever(similarity_top_k=2).retrieve("emerging demand")
    assert len(before) == 2
    assert {node.node.ref_doc_id for node in before} == {"doc-demand", "doc-backup"}
    assert all(node.node.metadata.get("source", "").startswith("fixture://") for node in before)

    index.storage_context.persist(persist_dir=str(PERSIST))
    tree_hash_before = hash_tree(PERSIST)
    restored = load_index_from_storage(StorageContext.from_defaults(persist_dir=str(PERSIST)), embed_model=embed)
    after = restored.as_retriever(similarity_top_k=2).retrieve("restore evidence")
    assert {node.node.ref_doc_id for node in after} == {"doc-demand", "doc-backup"}

    restored.delete_ref_doc("doc-backup", delete_from_docstore=True)
    remaining = restored.as_retriever(similarity_top_k=5).retrieve("backup receipts")
    assert all(node.node.ref_doc_id != "doc-backup" for node in remaining)
    restored.storage_context.persist(persist_dir=str(PERSIST))

    receipt = {
        "candidate": "llamaindex-core",
        "package_version": importlib.metadata.version("llama-index-core"),
        "status": "PASS",
        "offline": True,
        "embedding": "llama_index.core.embeddings.MockEmbedding(8)",
        "tests": {
            "document_ingest": True,
            "retrieval": True,
            "source_metadata_lineage": True,
            "persist": True,
            "reload": True,
            "delete_ref_doc": True,
        },
        "persisted_tree_sha256_before_delete": tree_hash_before,
        "remaining_ref_doc_ids": sorted({node.node.ref_doc_id for node in remaining}),
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
