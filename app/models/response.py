"""Raw LLM provider response model.

Represents an immutable, unparsed response captured directly from an external
LLM provider (OpenAI, Gemini). Preserving this raw record guarantees full data lineage
and auditability across subsequent analytical passes.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class RawLLMResponse(BaseModel):
    """Immutable record capturing the exact response and operational telemetry from an LLM call."""

    response_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this raw response record.",
    )
    audit_id: str = Field(
        ...,
        description="ID of the parent audit that generated this request.",
    )
    prompt_id: str = Field(
        ...,
        description="ID of the prompt submitted to the provider.",
    )
    run_id: str = Field(
        ...,
        description="Execution run identifier to support multi-run audits and prevent duplicate observations.",
    )
    provider: str = Field(
        ...,
        description="LLM provider name (e.g. 'openai', 'gemini').",
    )
    model: str = Field(
        ...,
        description="Exact model identifier returned by or requested from the provider.",
    )
    prompt_text: str = Field(
        ...,
        description="Verbatim prompt string submitted.",
    )
    response_text: str = Field(
        default="",
        description="Verbatim text output received from the model.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when the response was captured.",
    )
    latency_ms: float = Field(
        ...,
        description="Round-trip request latency in milliseconds.",
    )
    success: bool = Field(
        ...,
        description="Whether the provider request succeeded.",
    )
    error_message: str | None = Field(
        default=None,
        description="Detailed error message if the call failed.",
    )
    error_category: str | None = Field(
        default=None,
        description="Classification of error (e.g. 'timeout', 'rate_limit', 'auth_error', 'provider_error').",
    )
    provider_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific telemetry (e.g. finish_reason, token_usage, raw citations, grounding chunks). Secrets omitted.",
    )
