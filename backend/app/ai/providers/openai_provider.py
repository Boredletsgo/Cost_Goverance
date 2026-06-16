"""OpenAI provider."""
from __future__ import annotations

from typing import List

from app.ai.provider import ChatMessage, LLMProvider
from app.config import settings


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return resp.choices[0].message.content or ""
