"""GCP mock connector."""
from app.connectors.mock_base import JsonMockConnector


class GCPConnector(JsonMockConnector):
    name = "gcp"
    description = "Google Cloud Platform (mock) — billing, Compute Engine, SCC."
