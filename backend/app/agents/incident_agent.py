"""Incident Intelligence Agent — RCA, event correlation, impact assessment."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models
from app.agents.base import AgentResult, BaseAgent
from app.services.analytics import severity_rank


class IncidentIntelligenceAgent(BaseAgent):
    name = "incident"
    title = "Incident Intelligence Agent"
    system_prompt = (
        "You are the Incident Intelligence Agent for InfraMind. You perform root "
        "cause analysis by correlating incidents with the deployments and changes "
        "that preceded them on the same resource. State the probable cause, the "
        "blast radius, and whether remediation has been applied."
    )

    def analyze(self, db: Session) -> AgentResult:
        events = db.query(models.Event).order_by(models.Event.occurred_at).all()
        incidents = [e for e in events if e.kind == "incident"]
        changes = [e for e in events if e.kind in ("deploy", "change")]

        facts: list[str] = []
        insights: list[dict] = []

        for inc in sorted(incidents, key=lambda e: severity_rank(e.severity), reverse=True):
            # Correlate: most recent change on the same resource before the incident.
            candidates = [
                c
                for c in changes
                if c.resource_id == inc.resource_id and c.occurred_at <= inc.occurred_at
            ]
            cause = candidates[-1] if candidates else None
            remediation = next(
                (
                    e
                    for e in changes
                    if e.resource_id == inc.resource_id and e.occurred_at > inc.occurred_at
                ),
                None,
            )

            cause_txt = (
                f"likely triggered by '{cause.title}' ({cause.occurred_at})"
                if cause
                else "no preceding change found on the same resource"
            )
            rem_txt = (
                f" Remediation applied: '{remediation.title}'."
                if remediation
                else " No remediation recorded yet."
            )
            facts.append(
                f"Incident '{inc.title}' [{inc.severity}] on {inc.resource_id}: "
                f"{cause_txt}.{rem_txt}"
            )
            insights.append(
                {
                    "agent": self.name,
                    "kind": "rca",
                    "title": f"RCA: {inc.title}",
                    "summary": (
                        f"{inc.description} Probable cause: "
                        f"{cause.title if cause else 'unknown'}.{rem_txt}"
                    ),
                    "severity": inc.severity,
                    "confidence": 0.85 if cause else 0.4,
                    "impact_usd": 0.0,
                    "details": {
                        "incident": inc.external_id,
                        "resource": inc.resource_id,
                        "probable_cause": cause.external_id if cause else None,
                        "remediation": remediation.external_id if remediation else None,
                    },
                }
            )

        if not incidents:
            facts.append("No active incidents in the current window.")

        narrative = self._llm(
            "Provide a root-cause summary across the incidents below.\n"
            + "\n".join(f"- {f}" for f in facts)
        )
        return AgentResult(agent=self.name, narrative=narrative, facts=facts, insights=insights)
