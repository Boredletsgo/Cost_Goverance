"""Embedding functions for the vector store.

Defaults to local sentence-transformers (no API key). Falls back to a
deterministic hashing embedder if the model can't be loaded, so RAG still works
fully offline.
"""
from __future__ import annotations

import hashlib
import math
from functools import lru_cache
from typing import List

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_DIM = 384


class Embedder:
    def embed(self, texts: List[str]) -> List[List[float]]:  # pragma: no cover
        raise NotImplementedError


class HashingEmbedder(Embedder):
    """Deterministic bag-of-words hashing embedder (offline fallback)."""

    def __init__(self, dim: int = _DIM) -> None:
        self.dim = dim

    def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for token in text.lower().split():
                h = int(hashlib.md5(token.encode()).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()


class OpenAIEmbedder(Embedder):
    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: List[str]) -> List[List[float]]:
        resp = self._client.embeddings.create(
            model="text-embedding-3-small", input=texts
        )
        return [d.embedding for d in resp.data]


@lru_cache
def get_embedder() -> Embedder:
    try:
        if settings.embedding_provider == "openai" and settings.openai_api_key:
            return OpenAIEmbedder()
        return SentenceTransformerEmbedder(settings.embedding_model)
    except Exception as exc:
        logger.warning("Embedding model unavailable (%s); using hashing fallback.", exc)
        return HashingEmbedder()
