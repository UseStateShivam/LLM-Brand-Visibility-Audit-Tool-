"""Audit definition and state domain models.

Defines the configuration, targeting, providers, and lifecycle states
of a brand visibility audit.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.models.prompt import AuditPrompt


class AuditStatus(StrEnum):
    """Lifecycle status of an audit instance."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class ProviderSelection(BaseModel):
    """Configuration specifying an LLM provider and model pair to audit."""

    provider: str = Field(
        ...,
        description="Provider name (e.g., 'openai', 'gemini').",
    )
    model: str | None = Field(
        default=None,
        description="Specific model identifier. If omitted, provider default from environment is used.",
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Generation temperature (0.0 recommended for deterministic audit benchmarking).",
    )
    max_tokens: int = Field(
        default=1024,
        gt=0,
        description="Maximum tokens generated per prompt response.",
    )


class Audit(BaseModel):
    """Core domain model representing a complete brand visibility audit definition."""

    audit_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the audit instance.",
    )
    brand: str = Field(
        ...,
        min_length=1,
        description="Canonical target brand name (e.g. 'Acme AI').",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Known brand aliases, alternate spellings, or product names (e.g. ['Acme', 'AcmeAI']).",
    )
    brand_domain: str | None = Field(
        default=None,
        description="Primary domain of the brand (e.g. 'acme.ai') for distinguishing brand-owned citations.",
    )
    competitors: list[str] = Field(
        default_factory=list,
        description="List of competitor brand names to detect and benchmark against.",
    )
    industry: str = Field(
        default="technology",
        description="Industry or market sector (e.g. 'Customer Service AI', 'Fintech').",
    )
    topics: list[str] = Field(
        default_factory=lambda: ["general"],
        description="Audited topics or category clusters.",
    )
    prompts: list[AuditPrompt] = Field(
        default_factory=list,
        description="Structured list of prompts to execute across providers.",
    )
    providers: list[ProviderSelection] = Field(
        default_factory=list,
        description="List of provider and model configurations to evaluate.",
    )

    # Lifecycle & Audit Metadata
    status: AuditStatus = Field(
        default=AuditStatus.CREATED,
        description="Current processing status.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC creation timestamp.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC last update timestamp.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional custom tags or client metadata.",
    )
