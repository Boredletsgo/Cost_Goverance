"""Run agent sweeps and persist resulting insights."""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app import models
from app.agents.graph import full_sweep
from app.logging_config import get_logger

logger = get_logger(__name__)


def run_and_persist(db: Session, replace: bool = True) -> List[models.Insight]:
    """Run all agents and store their insights. Returns persisted rows."""
    if replace:
        db.query(models.Insight).delete()
        db.commit()

    results = full_sweep(db)
    persisted: List[models.Insight] = []
    for agent_name, result in results.items():
        for ins in result.insights:
            row = models.Insight(
                agent=ins["agent"],
                kind=ins["kind"],
                title=ins["title"],
                summary=ins["summary"],
                severity=ins.get("severity", "info"),
                confidence=float(ins.get("confidence", 0.0)),
                impact_usd=float(ins.get("impact_usd", 0.0)),
                details=ins.get("details", {}),
            )
            db.add(row)
            persisted.append(row)
    db.commit()
    logger.info("Persisted %d insights from sweep.", len(persisted))
    return persisted
