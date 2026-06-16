"""LangGraph orchestration for InfraMind.

Two flows:
- ``route_and_answer``: a StateGraph that classifies a user question, runs the
  best-fit specialized agent, and grounds the answer with RAG.
- ``full_sweep``: runs every agent for proactive, scheduled analysis.
"""
from __future__ import annotations

from typing import List, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.registry import AGENTS, get_agent
from app.logging_config import get_logger

logger = get_logger(__name__)

# Keyword router keeps routing deterministic and free (no LLM call required).
_ROUTING_KEYWORDS = {
    "cost": ["cost", "spend", "spent", "bill", "budget", "expensive", "price", "forecast", "anomaly", "increase"],
    "incident": ["incident", "outage", "root cause", "rca", "caused", "why did", "downtime", "latency", "crash", "error"],
    "security": ["security", "risk", "vulnerab", "cve", "exposed", "misconfig", "breach", "secret", "compliance"],
    "optimization": ["optimize", "optimise", "waste", "rightsize", "cleanup", "idle", "orphan", "savings", "efficien"],
    "executive": ["summary", "report", "executive", "overview", "weekly", "leadership", "business"],
}


def route_query(question: str) -> str:
    q = question.lower()
    scores = {
        agent: sum(1 for kw in kws if kw in q)
        for agent, kws in _ROUTING_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "executive"


class ChatState(TypedDict, total=False):
    question: str
    agent: str
    answer: str
    facts: List[str]
    insights: List[dict]
    citations: List[dict]
    trace: List[dict]
    _db: object


def _route_node(state: ChatState) -> ChatState:
    agent = state.get("agent") or route_query(state["question"])
    trace = state.get("trace", [])
    trace.append({"step": "route", "agent": agent})
    return {"agent": agent, "trace": trace}


def _agent_node(state: ChatState) -> ChatState:
    db: Session = state["_db"]  # type: ignore[assignment]
    agent = get_agent(state["agent"])
    result = agent.answer(db, state["question"])
    trace = state.get("trace", [])
    trace.append({"step": "analyze", "agent": agent.name, "facts": len(result.facts)})
    return {
        "answer": result.narrative,
        "facts": result.facts,
        "insights": result.insights,
        "citations": result.citations,
        "trace": trace,
    }


def _build_graph():
    g = StateGraph(ChatState)
    g.add_node("route", _route_node)
    g.add_node("agent", _agent_node)
    g.add_edge(START, "route")
    g.add_edge("route", "agent")
    g.add_edge("agent", END)
    return g.compile()


_GRAPH = _build_graph()


def route_and_answer(db: Session, question: str, agent: str | None = None) -> ChatState:
    state: ChatState = {"question": question, "trace": [], "_db": db}
    if agent:
        state["agent"] = agent
    result = _GRAPH.invoke(state)
    result.pop("_db", None)
    return result


def full_sweep(db: Session) -> dict:
    """Run all agents; return their results keyed by agent name."""
    results = {}
    for name, agent in AGENTS.items():
        try:
            res = agent.analyze(db)
            results[name] = res
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Agent %s failed: %s", name, exc)
    return results
