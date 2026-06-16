"""Mock LLM provider.

Produces grounded, deterministic narratives from the structured context the
agents pass in — so InfraMind is fully functional with **no API keys**. The
agents already compute findings deterministically in Python; this provider turns
those facts into readable prose.
"""
from __future__ import annotations

import re
from typing import List

from app.ai.provider import ChatMessage, LLMProvider


class MockProvider(LLMProvider):
    name = "mock"

    def complete(self, messages: List[ChatMessage], temperature: float = 0.2) -> str:
        system = " ".join(m.content for m in messages if m.role == "system").lower()
        user = "\n".join(m.content for m in messages if m.role == "user")

        role = "analysis"
        for key in ("cost", "incident", "security", "optimization", "executive"):
            if key in system:
                role = key
                break

        facts = self._extract_facts(user)
        intro = {
            "cost": "Cost analysis",
            "incident": "Incident root-cause analysis",
            "security": "Security risk assessment",
            "optimization": "Optimization review",
            "executive": "Executive summary",
            "analysis": "Analysis",
        }[role]

        lines = [f"**{intro}**", ""]
        if facts:
            lines.append("Based on the connected telemetry:")
            for f in facts[:8]:
                lines.append(f"- {f}")
        else:
            lines.append(
                "No significant anomalies were detected in the current window; "
                "key metrics are within their expected baselines."
            )

        lines += ["", self._closing(role)]
        return "\n".join(lines)

    @staticmethod
    def _extract_facts(text: str) -> List[str]:
        facts: List[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith(("-", "*", "•")):
                facts.append(line.lstrip("-*• ").strip())
            elif re.match(r"^\d+[\).]\s+", line):
                facts.append(re.sub(r"^\d+[\).]\s+", "", line))
        return facts

    @staticmethod
    def _closing(role: str) -> str:
        return {
            "cost": "Recommended next step: investigate the top driver above and "
            "apply the suggested optimization to recover spend.",
            "incident": "Recommended next step: correlate the change immediately "
            "preceding the incident and validate the remediation already applied.",
            "security": "Recommended next step: remediate critical findings first, "
            "prioritising internet-exposed and secret-related issues.",
            "optimization": "Recommended next step: action the highest-savings, "
            "lowest-risk items (orphaned and idle resources) first.",
            "executive": "Overall posture is stable with clear, actionable "
            "opportunities to reduce cost and risk this week.",
            "analysis": "Recommended next step: review the items above and action "
            "the highest-impact one first.",
        }[role]
