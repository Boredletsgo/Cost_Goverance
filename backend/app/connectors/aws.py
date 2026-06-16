"""AWS mock connector."""
from app.connectors.mock_base import JsonMockConnector


class AWSConnector(JsonMockConnector):
    name = "aws"
    description = "Amazon Web Services (mock) — Cost Explorer, EC2, S3, GuardDuty."
