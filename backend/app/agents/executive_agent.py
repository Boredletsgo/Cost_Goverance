"""Executive Intelligence Agent — business summaries and weekly reports."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models
from app.agents.base import AgentResult, BaseAgent
from app.services import analytics


class ExecutiveIntelligenceAgent(BaseAgent):
    name = "executive"
    title = "Executive Intelligence Agent"
    system_prompt = (
        "You are the Executive Intelligence Agent for InfraMind. You write concise "
        "executive summaries for engineering leadership: spend, risk, incidents, "
        "and savings opportunities, with clear business impact. Avoid jargon."
    )

    def analyze(self, db: Session) -> AgentResult:
        forecast = analytics.forecast_monthly(db)
        anomalies = analytics.detect_cost_anomalies(db)
        waste = analytics.find_waste(db)
        findings = db.query(models.SecurityFinding).all()
        incidents = db.query(models.Event).filter(models.Event.kind == "incident").all()

        crit = sum(1 for f in findings if f.severity == "critical")
        high = sum(1 for f in findings if f.severity == "high")
        savings = sum(w["monthly_savings"] for w in waste)
        anomaly_impact = sum(a["delta"] for a in anomalies)

        facts = [
            f"Projected 30-day spend: ${forecast['projected_30d']:,.0f} "
            f"(trend {forecast['trend_pct']:+.1f}%).",
            f"{len(anomalies)} cost anomalies detected, ~${anomaly_impact:,.0f} excess spend.",
            f"{len(incidents)} incidents; {crit} critical + {high} high security findings.",
            f"${savings:,.0f}/mo in identified savings opportunities.",
        ]

        insights = [
            {
                "agent": self.name,
                "kind": "summary",
                "title": "Weekly executive summary",
                "summary": " ".join(facts),
                "severity": "high" if crit else "info",
                "confidence": 0.8,
                "impact_usd": savings,
                "details": {
                    "forecast": forecast,
                    "anomaly_count": len(anomalies),
                    "critical_findings": crit,
                    "high_findings": high,
                    "incidents": len(incidents),
                    "monthly_savings": savings,
                },
            }
        ]

        narrative = self._llm(
            "Write a 4-6 sentence executive summary of infrastructure health, "
            "cost, risk, and the top recommended action.\n"
            + "\n".join(f"- {f}" for f in facts),
            temperature=0.3,
        )
        return AgentResult(agent=self.name, narrative=narrative, facts=facts, insights=insights)
