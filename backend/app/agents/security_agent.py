"""Security Intelligence Agent — risk prioritization and misconfiguration analysis."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models
from app.agents.base import AgentResult, BaseAgent
from app.services.analytics import severity_rank


class SecurityIntelligenceAgent(BaseAgent):
    name = "security"
    title = "Security Intelligence Agent"
    system_prompt = (
        "You are the Security Intelligence Agent for InfraMind. You prioritize "
        "findings by exploitability and blast radius. Internet-exposed management "
        "ports and exposed secrets are always top priority. Give a clear, ordered "
        "remediation plan."
    )

    def analyze(self, db: Session) -> AgentResult:
        findings = db.query(models.SecurityFinding).all()

        def risk_score(f: models.SecurityFinding) -> float:
            base = severity_rank(f.severity) * 2 + f.cvss
            if f.category in ("network", "secret"):
                base += 3  # internet exposure / secret leakage weighting
            return base

        ranked = sorted(findings, key=risk_score, reverse=True)
        facts: list[str] = []
        insights: list[dict] = []

        for f in ranked[:6]:
            facts.append(
                f"[{f.severity.upper()} cvss {f.cvss}] {f.title} "
                f"({f.category}, {f.connector}/{f.resource_id})."
            )

        for f in ranked[:4]:
            insights.append(
                {
                    "agent": self.name,
                    "kind": "recommendation",
                    "title": f"Security: {f.title}",
                    "summary": f"{f.description} Category: {f.category}. "
                    f"Resource: {f.resource_id}.",
                    "severity": f.severity,
                    "confidence": 0.9,
                    "impact_usd": 0.0,
                    "details": {
                        "finding": f.external_id,
                        "cvss": f.cvss,
                        "category": f.category,
                        "risk_score": round(risk_score(f), 1),
                    },
                }
            )

        counts = {s: sum(1 for f in findings if f.severity == s) for s in ("critical", "high", "medium", "low")}
        facts.insert(
            0,
            f"{counts['critical']} critical, {counts['high']} high, "
            f"{counts['medium']} medium findings open.",
        )

        narrative = self._llm(
            "Produce a prioritized remediation plan for these findings.\n"
            + "\n".join(f"- {f}" for f in facts)
        )
        return AgentResult(agent=self.name, narrative=narrative, facts=facts, insights=insights)
