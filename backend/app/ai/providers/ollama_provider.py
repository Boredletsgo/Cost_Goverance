"""Ollama provider (fully local, free)."""
from __future__ import annotations

from typing import List

import httpx

from app.ai.provider import ChatMessage, LLMProvider
from app.config import settings


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        self._base = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model

    def available(self) -> bool:
        try:
            r = httpx.get(f"{self._base}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        payload = {
            "model": self._model,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        r = httpx.post(f"{self._base}/api/chat", json=payload, timeout=120.0)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")
