"""Vendor-neutral LLM abstraction.

The rest of InfraMind depends only on ``LLMProvider``. Swap providers via the
``AI_PROVIDER`` env var with zero code changes. The ``mock`` provider makes the
platform fully functional with no API keys (free-tier / offline friendly).
"""
from app.ai.provider import LLMProvider, ChatMessage, get_llm

__all__ = ["LLMProvider", "ChatMessage", "get_llm"]
