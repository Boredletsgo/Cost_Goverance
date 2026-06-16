"""Kubernetes mock connector."""
from app.connectors.mock_base import JsonMockConnector


class KubernetesConnector(JsonMockConnector):
    name = "kubernetes"
    description = "Kubernetes (mock) — workloads, node cost allocation, events."
