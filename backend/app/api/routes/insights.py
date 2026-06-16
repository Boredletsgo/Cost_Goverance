"""Insight listing and filtering."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import InsightOut

router = APIRouter()


@router.get("", response_model=list[InsightOut])
def list_insights(
    agent: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> list[InsightOut]:
    q = db.query(models.Insight)
    if agent:
        q = q.filter(models.Insight.agent == agent)
    if kind:
        q = q.filter(models.Insight.kind == kind)
    if severity:
        q = q.filter(models.Insight.severity == severity)
    rows = q.order_by(models.Insight.impact_usd.desc(), models.Insight.created_at.desc()).limit(limit).all()
    return [InsightOut.model_validate(r) for r in rows]
