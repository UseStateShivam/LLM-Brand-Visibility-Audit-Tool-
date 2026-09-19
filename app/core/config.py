"""Application configuration module using Pydantic Settings.

Provides centralized, validated, and type-safe configuration loaded from
environment variables and optional .env files. Prevents ad-hoc os.environ
access across the application codebase.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings and environment configurations.

    Adheres to the 12-factor app methodology: configuration is stored in the
    environment and strictly validated upon startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Metadata & Runtime Environment
    app_name: str = "LLM Brand Visibility Audit Tool"
    app_version: str = "0.1.0"
    app_env: Literal["development", "testing", "staging", "production"] = (
        "development"
    )
    log_level: str = "INFO"

    # API Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Data Persistence Configuration
    # Uses relative path by default, resolved relative to workspace root
    data_dir: Path = Field(default=Path("data"))

    # LLM Provider Credentials
    # Optional at initialization so tests and mock runs do not fail if keys are missing
    openai_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)

    # Provider Default Models (overridable per audit or request)
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-1.5-flash"

    # Network, Concurrency & Resilience Controls
    request_timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_initial_delay_seconds: float = 1.0
    retry_backoff_factor: float = 2.0
    max_concurrent_requests: int = 5

    # Audit & Scoring Protocol Versions (for reproducibility)
    analysis_version: str = "1.0"
    scoring_version: str = "1.0"

    @property
    def audits_dir(self) -> Path:
        """Directory path for persisted audit definitions."""
        return self.data_dir / "audits"

    @property
    def raw_dir(self) -> Path:
        """Directory path for raw, immutable LLM responses."""
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        """Directory path for normalized observation records."""
        return self.data_dir / "processed"

    @property
    def reports_dir(self) -> Path:
        """Directory path for generated audit reports and client summaries."""
        return self.data_dir / "reports"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retrieve cached singleton instance of application settings.

    Using lru_cache avoids repeated file reads and validations on every
    dependency injection or helper call.
    """
    return Settings()
