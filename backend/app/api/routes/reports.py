"""Report generation and retrieval."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import ReportOut
from app.services.reports import build_weekly_report

router = APIRouter()


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db)) -> list[ReportOut]:
    rows = db.query(models.Report).order_by(models.Report.created_at.desc()).all()
    return [ReportOut.model_validate(r) for r in rows]


@router.post("/generate", response_model=ReportOut)
def generate(db: Session = Depends(get_db)) -> ReportOut:
    report = build_weekly_report(db)
    return ReportOut.model_validate(report)
