"""Google Gemini provider."""
from __future__ import annotations

from typing import List

from app.ai.provider import ChatMessage, LLMProvider
from app.config import settings


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        self._genai = genai
        self._model = settings.gemini_model

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        system = "\n".join(m.content for m in messages if m.role == "system")
        convo = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in messages if m.role != "system"
        )
        model = self._genai.GenerativeModel(
            self._model, system_instruction=system or None
        )
        resp = model.generate_content(
            convo, generation_config={"temperature": temperature}
        )
        return getattr(resp, "text", "") or ""
