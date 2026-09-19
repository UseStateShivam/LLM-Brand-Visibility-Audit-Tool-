"""Citation and source attribution models.

Represents structured source information extracted from LLM responses
(e.g., search grounding, URL citations, inline source markers).
Strictly adheres to the rule: missing citation data must not be represented
as zero citations, and domain URLs must never be fabricated.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CitationStatus(StrEnum):
    """Explicit status enumeration for citation extraction."""

    AVAILABLE = "AVAILABLE"
    NONE_FOUND = "NONE_FOUND"
    NOT_SUPPORTED_BY_PROVIDER = "NOT_SUPPORTED_BY_PROVIDER"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class CitationRecord(BaseModel):
    """Normalized citation record extracted from a provider response."""

    url: str = Field(
        ...,
        description="Verbatim source URL exposed by provider grounding or response metadata.",
    )
    domain: str = Field(
        ...,
        description="Clean domain name extracted from the URL (e.g. 'techcrunch.com').",
    )
    title: str | None = Field(
        default=None,
        description="Webpage or document title if exposed by the provider.",
    )
    citation_marker: str | None = Field(
        default=None,
        description="In-text citation marker if present (e.g. '[1]', '[source]').",
    )
    order_index: int = Field(
        default=0,
        description="Sequential index of appearance in provider sources.",
    )
    is_brand_owned: bool = Field(
        default=False,
        description="Flag indicating if the source domain matches the target brand's owned domain.",
    )
    extraction_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this citation record.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional provider grounding metadata (e.g., snippet text).",
    )
