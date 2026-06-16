"""Health and dashboard endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.ai import get_llm
from app.database import get_db
from app.rag import get_store
from app.schemas import DashboardSummary, InsightOut
from app.services import analytics

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": get_llm().name,
        "knowledge_docs": get_store().count(),
    }


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db)) -> DashboardSummary:
    forecast = analytics.forecast_monthly(db)
    waste = analytics.find_waste(db)
    timeseries = analytics.daily_totals(db)
    by_service = analytics.cost_by_service(db)[:8]

    resources = db.query(models.Resource).all()
    by_connector: dict[str, int] = {}
    for r in resources:
        by_connector[r.connector] = by_connector.get(r.connector, 0) + 1

    open_incidents = db.query(models.Event).filter(models.Event.kind == "incident").count()
    critical = db.query(models.SecurityFinding).filter(
        models.SecurityFinding.severity == "critical"
    ).count()
    active_insights = db.query(models.Insight).count()
    recent = (
        db.query(models.Insight)
        .order_by(models.Insight.created_at.desc())
        .limit(6)
        .all()
    )

    return DashboardSummary(
        total_monthly_cost=forecast["projected_30d"],
        cost_trend_pct=forecast["trend_pct"],
        open_incidents=open_incidents,
        critical_findings=critical,
        active_insights=active_insights,
        potential_savings_usd=round(sum(w["monthly_savings"] for w in waste), 2),
        resources_by_connector=by_connector,
        cost_by_service=by_service,
        cost_timeseries=timeseries,
        recent_insights=[InsightOut.model_validate(i) for i in recent],
    )
