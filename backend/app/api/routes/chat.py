"""Conversational endpoint backed by the LangGraph orchestrator."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.agents.graph import route_and_answer
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, InsightOut

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    # Ensure a conversation exists.
    conv = None
    if req.conversation_id:
        conv = db.get(models.Conversation, req.conversation_id)
    if conv is None:
        conv = models.Conversation(title=req.message[:60])
        db.add(conv)
        db.commit()
        db.refresh(conv)

    db.add(models.Message(conversation_id=conv.id, role="user", content=req.message))
    db.commit()

    state = route_and_answer(db, req.message, agent=req.agent)
    answer = state.get("answer", "")
    agent = state.get("agent", "executive")

    db.add(
        models.Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            agent=agent,
            meta={"citations": state.get("citations", [])},
        )
    )
    db.commit()

    insights = [InsightOut.model_validate({**i, "id": "", "status": "new", "created_at": conv.created_at}) for i in state.get("insights", [])]

    return ChatResponse(
        conversation_id=conv.id,
        agent=agent,
        answer=answer,
        citations=state.get("citations", []),
        insights=insights,
        trace=state.get("trace", []),
    )
