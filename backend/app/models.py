"""SQLAlchemy ORM models for InfraMind."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Resource(Base):
    """A cloud resource discovered through a connector."""

    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    connector: Mapped[str] = mapped_column(String, index=True)
    external_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, index=True)
    region: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="active")
    monthly_cost: Mapped[float] = mapped_column(Float, default=0.0)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class CostRecord(Base):
    """A daily cost data point per service/resource."""

    __tablename__ = "cost_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    connector: Mapped[str] = mapped_column(String, index=True)
    date: Mapped[str] = mapped_column(String, index=True)  # YYYY-MM-DD
    service: Mapped[str] = mapped_column(String, index=True)
    resource_id: Mapped[str] = mapped_column(String, default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String, default="USD")
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Event(Base):
    """An operational event (deployment, incident, alert, change)."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    connector: Mapped[str] = mapped_column(String, index=True)
    external_id: Mapped[str] = mapped_column(String, default="")
    kind: Mapped[str] = mapped_column(String, index=True)  # incident|deploy|alert|change
    severity: Mapped[str] = mapped_column(String, default="info")
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    resource_id: Mapped[str] = mapped_column(String, default="")
    occurred_at: Mapped[str] = mapped_column(String, index=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class SecurityFinding(Base):
    """A security finding / misconfiguration / vulnerability."""

    __tablename__ = "security_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    connector: Mapped[str] = mapped_column(String, index=True)
    external_id: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String, index=True)  # critical|high|medium|low
    category: Mapped[str] = mapped_column(String, default="")
    resource_id: Mapped[str] = mapped_column(String, default="")
    cvss: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="open")
    detected_at: Mapped[str] = mapped_column(String, index=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Insight(Base):
    """An AI-generated insight produced by an agent."""

    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    agent: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String, index=True)  # anomaly|recommendation|rca|summary|forecast
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String, default="info")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    impact_usd: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="new")
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String, default="New conversation")
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)  # user|assistant
    content: Mapped[str] = mapped_column(Text)
    agent: Mapped[str] = mapped_column(String, default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String, default="weekly")
    title: Mapped[str] = mapped_column(String)
    body_html: Mapped[str] = mapped_column(Text, default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    recipients: Mapped[str] = mapped_column(String, default="")
    sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=_now)
