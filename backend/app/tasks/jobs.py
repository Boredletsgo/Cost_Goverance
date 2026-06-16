"""Celery tasks that power InfraMind's proactive intelligence loop."""
from __future__ import annotations

from app.database import SessionLocal
from app.logging_config import get_logger
from app.rag.ingest import ingest_db_records, ingest_knowledge_base
from app.services.ingestion import ingest_all
from app.services.insights import run_and_persist
from app.services.reports import build_weekly_report
from app.worker import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.jobs.refresh_and_analyze")
def refresh_and_analyze() -> dict:
    """Pull connectors, re-index RAG, run all agents, persist insights."""
    db = SessionLocal()
    try:
        counts = ingest_all(db)
        ingest_knowledge_base()
        ingest_db_records(db)
        insights = run_and_persist(db, replace=True)
        return {"ingested": counts, "insights": len(insights)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.jobs.send_weekly_report")
def send_weekly_report() -> dict:
    db = SessionLocal()
    try:
        report = build_weekly_report(db)
        return {"report_id": report.id, "sent": bool(report.sent)}
    finally:
        db.close()
