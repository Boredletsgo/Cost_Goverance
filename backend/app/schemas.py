"""Pydantic schemas for API serialization."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResourceOut(ORMModel):
    id: str
    connector: str
    external_id: str
    name: str
    type: str
    region: str
    status: str
    monthly_cost: float
    tags: dict
    attributes: dict


class CostRecordOut(ORMModel):
    id: str
    connector: str
    date: str
    service: str
    resource_id: str
    amount: float
    currency: str


class EventOut(ORMModel):
    id: str
    connector: str
    kind: str
    severity: str
    title: str
    description: str
    resource_id: str
    occurred_at: str
    meta: dict


class SecurityFindingOut(ORMModel):
    id: str
    connector: str
    title: str
    description: str
    severity: str
    category: str
    resource_id: str
    cvss: float
    status: str
    detected_at: str


class InsightOut(ORMModel):
    id: str
    agent: str
    kind: str
    title: str
    summary: str
    severity: str
    confidence: float
    impact_usd: float
    details: dict
    status: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    agent: Optional[str] = None  # force a specific agent, else orchestrator routes


class ChatResponse(BaseModel):
    conversation_id: str
    agent: str
    answer: str
    citations: List[dict] = []
    insights: List[InsightOut] = []
    trace: List[dict] = []


class AgentRunRequest(BaseModel):
    agent: str
    persist: bool = True


class AgentRunResponse(BaseModel):
    agent: str
    insights: List[InsightOut]
    summary: str


class ConnectorInfo(BaseModel):
    name: str
    enabled: bool
    capabilities: List[str]
    description: str


class DashboardSummary(BaseModel):
    total_monthly_cost: float
    cost_trend_pct: float
    open_incidents: int
    critical_findings: int
    active_insights: int
    potential_savings_usd: float
    resources_by_connector: dict
    cost_by_service: List[dict]
    cost_timeseries: List[dict]
    recent_insights: List[InsightOut]


class ReportOut(ORMModel):
    id: str
    kind: str
    title: str
    body_html: str
    recipients: str
    sent: int
    created_at: datetime


class ActionResult(BaseModel):
    ok: bool
    detail: str
    data: Any = None
