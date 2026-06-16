"""Celery application + beat schedule for proactive analysis."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings
from app.logging_config import configure_logging

configure_logging()

celery_app = Celery(
    "inframind",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Proactive, autonomous schedule: ingest + analyze frequently, report weekly.
celery_app.conf.beat_schedule = {
    "refresh-and-analyze": {
        "task": "app.tasks.jobs.refresh_and_analyze",
        "schedule": crontab(minute="*/15"),
    },
    "weekly-executive-report": {
        "task": "app.tasks.jobs.send_weekly_report",
        "schedule": crontab(minute=0, hour=8, day_of_week="mon"),
    },
}

# Ensure tasks are registered.
from app.tasks import jobs  # noqa: E402,F401
