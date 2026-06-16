"""Connector registry — discovery and lifecycle for all connectors.

Each connector can run in two modes:

* ``mock`` — bundled sample data (zero config, the default).
* ``live`` — real cloud APIs via the vendor SDK.

The effective mode is resolved at runtime from :mod:`app.connectors.runtime`
(which the Setup page can toggle), falling back to the mock class whenever a live
implementation or its SDK is unavailable.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Type

from app.config import settings
from app.connectors import runtime
from app.connectors.aws import AWSConnector
from app.connectors.aws_live import AWSLiveConnector
from app.connectors.azure import AzureConnector
from app.connectors.azure_live import AzureLiveConnector
from app.connectors.base import BaseConnector
from app.connectors.gcp import GCPConnector
from app.connectors.github import GitHubConnector
from app.connectors.kubernetes import KubernetesConnector
from app.logging_config import get_logger

logger = get_logger(__name__)

# Mock (default) implementations.
_REGISTRY: Dict[str, Type[BaseConnector]] = {
    AzureConnector.name: AzureConnector,
    AWSConnector.name: AWSConnector,
    GCPConnector.name: GCPConnector,
    KubernetesConnector.name: KubernetesConnector,
    GitHubConnector.name: GitHubConnector,
}

# Live implementations, where available.
_LIVE_REGISTRY: Dict[str, Type[BaseConnector]] = {
    AzureLiveConnector.name: AzureLiveConnector,
    AWSLiveConnector.name: AWSLiveConnector,
}


class ConnectorRegistry:
    def register(self, connector_cls: Type[BaseConnector], live: bool = False) -> None:
        (_LIVE_REGISTRY if live else _REGISTRY)[connector_cls.name] = connector_cls

    def all_names(self) -> List[str]:
        return list(_REGISTRY.keys())

    def live_class(self, name: str) -> Optional[Type[BaseConnector]]:
        return _LIVE_REGISTRY.get(name)

    def has_live(self, name: str) -> bool:
        return name in _LIVE_REGISTRY

    def mode(self, name: str) -> str:
        """Effective mode for a connector, degrading to mock if live is unusable."""
        if runtime.get_mode(name) != "live":
            return "mock"
        cls = _LIVE_REGISTRY.get(name)
        if cls is None:
            return "mock"
        sdk_ok = getattr(cls, "sdk_available", lambda: True)()
        return "live" if sdk_ok else "mock"

    def get(self, name: str) -> BaseConnector:
        if name not in _REGISTRY:
            raise KeyError(f"Unknown connector: {name}")
        if self.mode(name) == "live":
            return _LIVE_REGISTRY[name]()
        return _REGISTRY[name]()

    def is_enabled(self, name: str) -> bool:
        return name in settings.connectors_list

    def enabled(self) -> List[BaseConnector]:
        return [self.get(n) for n in settings.connectors_list if n in _REGISTRY]


registry = ConnectorRegistry()


def get_connector(name: str) -> BaseConnector:
    return registry.get(name)


def get_enabled_connectors() -> List[BaseConnector]:
    return registry.enabled()
