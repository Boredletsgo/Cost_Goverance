"""Central configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database / cache
    database_url: str = "sqlite:///./.data/inframind.db"
    redis_url: str = "redis://localhost:6379/0"

    # Vector store
    chroma_persist_dir: str = "./.data/chroma"

    # AI providers
    ai_provider: str = "mock"  # openai | gemini | ollama | mock
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Embeddings
    embedding_provider: str = "local"  # local | openai
    embedding_model: str = "all-MiniLM-L6-v2"

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "inframind@localhost"
    report_recipients: str = "ops@example.com"

    # Connectors
    enabled_connectors: str = "azure,aws,gcp,kubernetes,github"

    # Per-connector data mode: "mock" (bundled sample data) or "live" (real cloud APIs).
    # These are the *defaults*; the Setup page can override them at runtime.
    azure_mode: str = "mock"
    aws_mode: str = "mock"
    gcp_mode: str = "mock"
    kubernetes_mode: str = "mock"
    github_mode: str = "mock"

    # --- Azure credentials (live mode) ---
    # If client_id/secret/tenant are set they are used; otherwise DefaultAzureCredential
    # falls back to `az login`, managed identity, env vars, etc.
    azure_subscription_id: str = ""
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # --- AWS credentials (live mode) ---
    # If access keys are set they are used; otherwise boto3's default chain
    # (shared profile / env / instance role) applies.
    aws_region: str = "us-east-1"
    aws_profile: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""

    @property
    def connectors_list(self) -> List[str]:
        return [c.strip() for c in self.enabled_connectors.split(",") if c.strip()]

    def connector_mode(self, name: str) -> str:
        """Default data mode for a connector (overridable at runtime)."""
        return getattr(self, f"{name}_mode", "mock") or "mock"

    @property
    def recipients_list(self) -> List[str]:
        return [r.strip() for r in self.report_recipients.split(",") if r.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
