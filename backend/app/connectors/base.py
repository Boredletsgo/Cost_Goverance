"""Base connector interface shared by every integration."""
from __future__ import annotations

import abc
from enum import Enum
from typing import Any, Dict, List


class ConnectorCapability(str, Enum):
    COST = "cost"
    RESOURCES = "resources"
    EVENTS = "events"
    SECURITY = "security"
    ACTIONS = "actions"


class BaseConnector(abc.ABC):
    """Abstract base every connector must implement.

    The contract is intentionally small and uniform so the rest of the platform
    (ingestion, agents, RAG) is fully decoupled from any specific vendor SDK.
    """

    #: Stable connector identifier, e.g. "azure", "aws".
    name: str = "base"
    #: Human-friendly description shown in the UI.
    description: str = ""
    #: Capabilities this connector supports.
    capabilities: List[ConnectorCapability] = []

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abc.abstractmethod
    async def get_cost_data(self) -> List[Dict[str, Any]]:
        """Return normalized daily cost records.

        Each item: ``{date, service, resource_id, amount, currency}``.
        """

    @abc.abstractmethod
    async def get_resources(self) -> List[Dict[str, Any]]:
        """Return normalized resource inventory.

        Each item: ``{external_id, name, type, region, status, monthly_cost,
        tags, attributes}``.
        """

    @abc.abstractmethod
    async def get_events(self) -> List[Dict[str, Any]]:
        """Return normalized operational events.

        Each item: ``{external_id, kind, severity, title, description,
        resource_id, occurred_at, meta}``.
        """

    @abc.abstractmethod
    async def get_security_findings(self) -> List[Dict[str, Any]]:
        """Return normalized security findings.

        Each item: ``{external_id, title, description, severity, category,
        resource_id, cvss, status, detected_at, meta}``.
        """

    @abc.abstractmethod
    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a remediation/optimization action.

        Returns ``{ok, detail, data}``. Mock connectors simulate the effect.
        """

    def supports(self, capability: ConnectorCapability) -> bool:
        return capability in self.capabilities
