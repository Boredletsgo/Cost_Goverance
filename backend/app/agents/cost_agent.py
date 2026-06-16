"""Cost Intelligence Agent — anomaly detection, forecasting, waste, optimization."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.base import AgentResult, BaseAgent
from app.services import analytics


class CostIntelligenceAgent(BaseAgent):
    name = "cost"
    title = "Cost Intelligence Agent"
    system_prompt = (
        "You are the Cost Intelligence Agent for InfraMind. You detect cost "
        "anomalies, forecast spend, and recommend optimizations. Be specific, "
        "quantify impact in dollars, and reference the responsible resource."
    )

    def analyze(self, db: Session) -> AgentResult:
        anomalies = analytics.detect_cost_anomalies(db)
        forecast = analytics.forecast_monthly(db)
        waste = analytics.find_waste(db)

        facts: list[str] = []
        insights: list[dict] = []

        for a in anomalies[:5]:
            facts.append(
                f"Cost spike on {a['service']} ({a['connector']}) on {a['date']}: "
                f"${a['amount']:.0f} vs ${a['baseline']:.0f} baseline "
                f"(+{a['increase_pct']:.0f}%, +${a['delta']:.0f}), z={a['z_score']}."
            )
            insights.append(
                {
                    "agent": self.name,
                    "kind": "anomaly",
                    "title": f"Cost anomaly: {a['service']} +{a['increase_pct']:.0f}% on {a['date']}",
                    "summary": (
                        f"{a['service']} on {a['connector']} spent ${a['amount']:.0f} "
                        f"vs a ${a['baseline']:.0f} baseline (+${a['delta']:.0f}). "
                        f"Resource: {a['resource_id']}."
                    ),
                    "severity": "high" if a["increase_pct"] > 100 else "medium",
                    "confidence": min(0.95, 0.6 + a["z_score"] / 20),
                    "impact_usd": a["delta"],
                    "details": a,
                }
            )

        run_rate = forecast["projected_30d"]
        facts.append(
            f"30-day spend forecast: ${run_rate:,.0f} at current run rate "
            f"(trend {forecast['trend_pct']:+.1f}%)."
        )
        insights.append(
            {
                "agent": self.name,
                "kind": "forecast",
                "title": f"Projected 30-day spend ${run_rate:,.0f}",
                "summary": f"Daily run rate ${forecast['daily_run_rate']:,.0f}, "
                f"trend {forecast['trend_pct']:+.1f}% vs prior period.",
                "severity": "info",
                "confidence": 0.7,
                "impact_usd": 0.0,
                "details": forecast,
            }
        )

        total_waste = sum(w["monthly_savings"] for w in waste)
        if waste:
            facts.append(
                f"Identified ${total_waste:,.0f}/mo of potential waste across "
                f"{len(waste)} resources (orphaned/idle/over-provisioned)."
            )

        narrative = self._llm(
            "Summarize the cost posture and the single most important action.\n"
            + "\n".join(f"- {f}" for f in facts)
        )
        return AgentResult(agent=self.name, narrative=narrative, facts=facts, insights=insights)
