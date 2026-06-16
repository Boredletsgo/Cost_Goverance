"""ChromaDB-backed knowledge store for infrastructure RAG search."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List

from app.ai.embeddings import get_embedder
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_COLLECTION = "inframind_knowledge"


class KnowledgeStore:
    """Thin wrapper over a persistent Chroma collection.

    Embeddings are computed by InfraMind's own ``Embedder`` so the same model is
    used everywhere and the store works offline.
    """

    def __init__(self) -> None:
        import chromadb

        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._embedder = get_embedder()
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def add(self, documents: List[Dict]) -> int:
        """Upsert documents. Each: ``{id, text, metadata}``."""
        if not documents:
            return 0
        ids = [d["id"] for d in documents]
        texts = [d["text"] for d in documents]
        metas = [d.get("metadata", {}) for d in documents]
        embeddings = self._embedder.embed(texts)
        self._collection.upsert(
            ids=ids, documents=texts, embeddings=embeddings, metadatas=metas
        )
        return len(ids)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if self.count() == 0:
            return []
        emb = self._embedder.embed([query])[0]
        res = self._collection.query(
            query_embeddings=[emb],
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        out: List[Dict] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            out.append(
                {
                    "text": doc,
                    "metadata": meta,
                    "score": round(1.0 - float(dist), 4),
                }
            )
        return out

    def count(self) -> int:
        try:
            return self._collection.count()
        except Exception:
            return 0

    def reset(self) -> None:
        try:
            self._client.delete_collection(_COLLECTION)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION, metadata={"hnsw:space": "cosine"}
        )


@lru_cache
def get_store() -> KnowledgeStore:
    return KnowledgeStore()
