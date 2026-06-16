"""Connector registry — discovery and lifecycle for all connectors."""
from __future__ import annotations

from typing import Dict, List, Type

from app.config import settings
from app.connectors.aws import AWSConnector
from app.connectors.azure import AzureConnector
from app.connectors.base import BaseConnector
from app.connectors.gcp import GCPConnector
from app.connectors.github import GitHubConnector
from app.connectors.kubernetes import KubernetesConnector

# Register every known connector class here. Third-party connectors can extend
# this mapping at runtime via ``registry.register``.
_REGISTRY: Dict[str, Type[BaseConnector]] = {
    AzureConnector.name: AzureConnector,
    AWSConnector.name: AWSConnector,
    GCPConnector.name: GCPConnector,
    KubernetesConnector.name: KubernetesConnector,
    GitHubConnector.name: GitHubConnector,
}


class ConnectorRegistry:
    def register(self, connector_cls: Type[BaseConnector]) -> None:
        _REGISTRY[connector_cls.name] = connector_cls

    def all_names(self) -> List[str]:
        return list(_REGISTRY.keys())

    def get(self, name: str) -> BaseConnector:
        if name not in _REGISTRY:
            raise KeyError(f"Unknown connector: {name}")
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
