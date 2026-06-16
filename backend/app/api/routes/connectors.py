"""Connector management and data refresh."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.connectors import registry
from app.connectors.base import ConnectorCapability
from app.database import get_db
from app.rag.ingest import ingest_db_records, ingest_knowledge_base
from app.schemas import (
    ActionResult,
    ConnectorInfo,
    CostRecordOut,
    EventOut,
    ResourceOut,
    SecurityFindingOut,
)
from app.services.ingestion import ingest_all

router = APIRouter()


@router.get("", response_model=list[ConnectorInfo])
def list_connectors() -> list[ConnectorInfo]:
    infos = []
    for name in registry.all_names():
        conn = registry.get(name)
        infos.append(
            ConnectorInfo(
                name=conn.name,
                enabled=registry.is_enabled(conn.name),
                capabilities=[c.value for c in conn.capabilities],
                description=conn.description,
            )
        )
    return infos


@router.post("/refresh")
def refresh(db: Session = Depends(get_db)) -> dict:
    counts = ingest_all(db)
    ingest_knowledge_base()
    ingest_db_records(db)
    return {"status": "refreshed", "counts": counts}


@router.get("/resources", response_model=list[ResourceOut])
def resources(db: Session = Depends(get_db)) -> list[ResourceOut]:
    return [ResourceOut.model_validate(r) for r in db.query(models.Resource).all()]


@router.get("/costs", response_model=list[CostRecordOut])
def costs(db: Session = Depends(get_db)) -> list[CostRecordOut]:
    return [CostRecordOut.model_validate(r) for r in db.query(models.CostRecord).all()]


@router.get("/events", response_model=list[EventOut])
def events(db: Session = Depends(get_db)) -> list[EventOut]:
    rows = db.query(models.Event).order_by(models.Event.occurred_at.desc()).all()
    return [EventOut.model_validate(r) for r in rows]


@router.get("/findings", response_model=list[SecurityFindingOut])
def findings(db: Session = Depends(get_db)) -> list[SecurityFindingOut]:
    return [SecurityFindingOut.model_validate(r) for r in db.query(models.SecurityFinding).all()]


@router.post("/{name}/action", response_model=ActionResult)
async def execute_action(name: str, action: str, params: dict | None = None) -> ActionResult:
    try:
        conn = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown connector: {name}")
    if not conn.supports(ConnectorCapability.ACTIONS):
        raise HTTPException(status_code=400, detail="Connector does not support actions")
    result = await conn.execute_action(action, params or {})
    return ActionResult(ok=result["ok"], detail=result["detail"], data=result.get("data"))
