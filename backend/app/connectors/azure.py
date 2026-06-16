"""Azure mock connector."""
from app.connectors.mock_base import JsonMockConnector


class AzureConnector(JsonMockConnector):
    name = "azure"
    description = "Microsoft Azure (mock) — subscriptions, cost, resources, advisor."
