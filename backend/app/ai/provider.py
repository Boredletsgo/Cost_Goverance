"""LLM provider interface and factory."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from functools import lru_cache
from typing import List

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


class LLMProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        """Return a single text completion for the given messages."""

    def available(self) -> bool:  # pragma: no cover - trivial
        return True


def _build_provider(provider: str) -> LLMProvider:
    provider = (provider or "mock").lower()
    try:
        if provider == "openai" and settings.openai_api_key:
            from app.ai.providers.openai_provider import OpenAIProvider

            return OpenAIProvider()
        if provider == "gemini" and settings.gemini_api_key:
            from app.ai.providers.gemini_provider import GeminiProvider

            return GeminiProvider()
        if provider == "ollama":
            from app.ai.providers.ollama_provider import OllamaProvider

            ollama = OllamaProvider()
            if ollama.available():
                return ollama
            logger.warning("Ollama not reachable; falling back to mock provider.")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to init provider '%s' (%s); using mock.", provider, exc)

    from app.ai.providers.mock_provider import MockProvider

    return MockProvider()


@lru_cache
def get_llm() -> LLMProvider:
    provider = _build_provider(settings.ai_provider)
    logger.info("LLM provider initialized: %s", provider.name)
    return provider
