"""Agent endpoints — list agents and run them on demand."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.registry import AGENTS, get_agent
from app.database import get_db
from app.schemas import AgentRunResponse, InsightOut
from app.services.insights import run_and_persist

router = APIRouter()


@router.get("")
def list_agents() -> list[dict]:
    return [
        {"name": a.name, "title": a.title, "description": a.system_prompt}
        for a in AGENTS.values()
    ]


@router.post("/{agent_name}/run", response_model=AgentRunResponse)
def run_agent(agent_name: str, db: Session = Depends(get_db)) -> AgentRunResponse:
    try:
        agent = get_agent(agent_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")

    result = agent.analyze(db)
    insights = [
        InsightOut.model_validate(
            {**i, "id": "", "status": "new", "created_at": datetime.now(timezone.utc)}
        )
        for i in result.insights
    ]
    return AgentRunResponse(agent=agent.name, insights=insights, summary=result.narrative)


@router.post("/sweep", response_model=list[InsightOut])
def run_sweep(db: Session = Depends(get_db)) -> list[InsightOut]:
    """Run every agent and persist insights (proactive analysis on demand)."""
    persisted = run_and_persist(db, replace=True)
    return [InsightOut.model_validate(i) for i in persisted]
