"""Base agent abstraction."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import List

from sqlalchemy.orm import Session

from app.ai import ChatMessage, get_llm
from app.rag import get_store


@dataclass
class AgentResult:
    agent: str
    narrative: str
    facts: List[str] = field(default_factory=list)
    insights: List[dict] = field(default_factory=list)
    citations: List[dict] = field(default_factory=list)


class BaseAgent(abc.ABC):
    name: str = "base"
    title: str = "Base Agent"
    system_prompt: str = "You are an infrastructure analysis assistant."

    @abc.abstractmethod
    def analyze(self, db: Session) -> AgentResult:
        """Run the agent's deterministic analysis and produce insights."""

    def answer(self, db: Session, question: str) -> AgentResult:
        """Answer a free-form question grounded in this agent's analysis + RAG."""
        result = self.analyze(db)
        citations = get_store().search(question, k=4)
        result.citations = citations
        context = "\n".join(f"- {c['text']}" for c in citations)
        facts = "\n".join(f"- {f}" for f in result.facts) or "- No notable findings."
        prompt = (
            f"User question: {question}\n\n"
            f"Findings from live telemetry:\n{facts}\n\n"
            f"Relevant knowledge base context:\n{context or '- (none)'}\n\n"
            "Answer the question concisely and concretely using the findings above."
        )
        result.narrative = self._llm(prompt)
        return result

    def _llm(self, user_prompt: str, temperature: float = 0.2) -> str:
        return get_llm().complete(
            [
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ],
            temperature=temperature,
        )
