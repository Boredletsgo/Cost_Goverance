"""Connector framework.

All integrations (cloud providers, K8s, GitHub, observability tools) implement
``BaseConnector``. This keeps InfraMind cloud-agnostic and vendor-neutral: the
agents and ingestion pipeline only ever talk to this interface.
"""
from app.connectors.base import BaseConnector, ConnectorCapability
from app.connectors.registry import get_connector, get_enabled_connectors, registry

__all__ = [
    "BaseConnector",
    "ConnectorCapability",
    "registry",
    "get_connector",
    "get_enabled_connectors",
]
