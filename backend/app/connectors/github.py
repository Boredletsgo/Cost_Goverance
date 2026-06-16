"""GitHub mock connector."""
from app.connectors.mock_base import JsonMockConnector


class GitHubConnector(JsonMockConnector):
    name = "github"
    description = "GitHub (mock) — deployments, Dependabot/code-scanning alerts."
