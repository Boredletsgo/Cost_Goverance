"""JSON-backed mock connector base.

Loads realistic datasets from ``app/connectors/data/<name>/*.json`` so the entire
platform works with zero cloud credentials. Real connectors would replace the
``_load`` calls with live SDK/API calls while keeping the same normalized output.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from app.connectors.base import BaseConnector, ConnectorCapability

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class JsonMockConnector(BaseConnector):
    """Base class for mock connectors that read from bundled JSON datasets."""

    capabilities = [
        ConnectorCapability.COST,
        ConnectorCapability.RESOURCES,
        ConnectorCapability.EVENTS,
        ConnectorCapability.SECURITY,
        ConnectorCapability.ACTIONS,
    ]

    def _load(self, dataset: str) -> List[Dict[str, Any]]:
        path = os.path.join(_DATA_DIR, self.name, f"{dataset}.json")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    async def get_cost_data(self) -> List[Dict[str, Any]]:
        return self._load("cost")

    async def get_resources(self) -> List[Dict[str, Any]]:
        return self._load("resources")

    async def get_events(self) -> List[Dict[str, Any]]:
        return self._load("events")

    async def get_security_findings(self) -> List[Dict[str, Any]]:
        return self._load("security")

    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Mock connectors simulate the action without mutating real infra.
        return {
            "ok": True,
            "detail": f"[{self.name}] simulated action '{action}'",
            "data": {"action": action, "params": params, "simulated": True},
        }
