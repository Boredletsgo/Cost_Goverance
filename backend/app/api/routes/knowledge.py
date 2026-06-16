"""RAG-powered infrastructure knowledge search."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.rag import get_store
from app.rag.ingest import ingest_db_records, ingest_knowledge_base

router = APIRouter()


@router.get("/search")
def search(q: str = Query(..., min_length=2), k: int = Query(5, le=20)) -> dict:
    results = get_store().search(q, k=k)
    return {"query": q, "results": results, "total_docs": get_store().count()}


@router.post("/reindex")
def reindex(db: Session = Depends(get_db)) -> dict:
    kb = ingest_knowledge_base()
    db_docs = ingest_db_records(db)
    return {"knowledge_base": kb, "db_records": db_docs, "total": get_store().count()}
