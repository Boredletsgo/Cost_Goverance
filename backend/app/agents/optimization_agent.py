"""Optimization Agent — cleanup, rightsizing, efficiency recommendations."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.base import AgentResult, BaseAgent
from app.services import analytics


class OptimizationAgent(BaseAgent):
    name = "optimization"
    title = "Optimization Agent"
    system_prompt = (
        "You are the Optimization Agent for InfraMind. You recommend resource "
        "cleanup and rightsizing ranked by savings and risk. Prefer the safest, "
        "highest-savings actions first (orphaned and idle resources)."
    )

    def analyze(self, db: Session) -> AgentResult:
        waste = analytics.find_waste(db)
        facts: list[str] = []
        insights: list[dict] = []

        total = sum(w["monthly_savings"] for w in waste)
        facts.append(
            f"Total identified savings: ${total:,.0f}/mo across {len(waste)} resources."
        )

        for w in waste[:8]:
            facts.append(
                f"{w['name']} ({w['type']}, {w['connector']}): {w['reason']} — "
                f"save ${w['monthly_savings']:,.0f}/mo."
            )

        for w in waste[:6]:
            risk = "low" if "orphaned" in w["reason"] or "idle" in w["reason"] else "medium"
            insights.append(
                {
                    "agent": self.name,
                    "kind": "recommendation",
                    "title": f"Optimize {w['name']}: {w['reason']}",
                    "summary": f"{w['type']} on {w['connector']} ({w['resource_id']}) — "
                    f"{w['reason']}. Estimated savings ${w['monthly_savings']:,.0f}/mo.",
                    "severity": "info",
                    "confidence": 0.85,
                    "impact_usd": w["monthly_savings"],
                    "details": {**w, "risk": risk},
                }
            )

        narrative = self._llm(
            "Recommend the top optimization actions ordered by savings and safety.\n"
            + "\n".join(f"- {f}" for f in facts)
        )
        return AgentResult(agent=self.name, narrative=narrative, facts=facts, insights=insights)
