"""Ingestion: pull data from enabled connectors into the database."""
from __future__ import annotations

import asyncio
from typing import Dict

from sqlalchemy.orm import Session

from app import models
from app.connectors import get_enabled_connectors
from app.logging_config import get_logger

logger = get_logger(__name__)


async def _collect(connector) -> Dict[str, list]:
    cost, resources, events, security = await asyncio.gather(
        connector.get_cost_data(),
        connector.get_resources(),
        connector.get_events(),
        connector.get_security_findings(),
    )
    return {
        "cost": cost,
        "resources": resources,
        "events": events,
        "security": security,
    }


def ingest_all(db: Session) -> Dict[str, int]:
    """Full refresh: clears connector-sourced tables and reloads from connectors."""
    counts = {"resources": 0, "cost": 0, "events": 0, "security": 0}

    # Idempotent full refresh
    db.query(models.CostRecord).delete()
    db.query(models.Resource).delete()
    db.query(models.Event).delete()
    db.query(models.SecurityFinding).delete()
    db.commit()

    for connector in get_enabled_connectors():
        data = asyncio.run(_collect(connector))

        for row in data["resources"]:
            db.add(
                models.Resource(
                    connector=connector.name,
                    external_id=row.get("external_id", ""),
                    name=row.get("name", ""),
                    type=row.get("type", ""),
                    region=row.get("region", ""),
                    status=row.get("status", "active"),
                    monthly_cost=float(row.get("monthly_cost", 0.0)),
                    tags=row.get("tags", {}),
                    attributes=row.get("attributes", {}),
                )
            )
            counts["resources"] += 1

        for row in data["cost"]:
            db.add(
                models.CostRecord(
                    connector=connector.name,
                    date=row.get("date", ""),
                    service=row.get("service", ""),
                    resource_id=row.get("resource_id", ""),
                    amount=float(row.get("amount", 0.0)),
                    currency=row.get("currency", "USD"),
                )
            )
            counts["cost"] += 1

        for row in data["events"]:
            db.add(
                models.Event(
                    connector=connector.name,
                    external_id=row.get("external_id", ""),
                    kind=row.get("kind", "event"),
                    severity=row.get("severity", "info"),
                    title=row.get("title", ""),
                    description=row.get("description", ""),
                    resource_id=row.get("resource_id", ""),
                    occurred_at=row.get("occurred_at", ""),
                    meta=row.get("meta", {}),
                )
            )
            counts["events"] += 1

        for row in data["security"]:
            db.add(
                models.SecurityFinding(
                    connector=connector.name,
                    external_id=row.get("external_id", ""),
                    title=row.get("title", ""),
                    description=row.get("description", ""),
                    severity=row.get("severity", "low"),
                    category=row.get("category", ""),
                    resource_id=row.get("resource_id", ""),
                    cvss=float(row.get("cvss", 0.0)),
                    status=row.get("status", "open"),
                    detected_at=row.get("detected_at", ""),
                    meta=row.get("meta", {}),
                )
            )
            counts["security"] += 1

    db.commit()
    logger.info("Ingestion complete: %s", counts)
    return counts
