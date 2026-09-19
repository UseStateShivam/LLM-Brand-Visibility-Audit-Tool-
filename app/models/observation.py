"""Observation domain models.

Captures the normalized analytical outputs derived from evaluating a single
raw LLM response against the target brand, aliases, and competitor entities.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.models.citation import CitationRecord, CitationStatus


class RecommendationClass(StrEnum):
    """Classification of brand recommendation stance in an answer."""

    ABSENT = "ABSENT"
    MENTIONED = "MENTIONED"
    RECOMMENDED = "RECOMMENDED"
    STRONGLY_RECOMMENDED = "STRONGLY_RECOMMENDED"


class MentionContext(BaseModel):
    """Surrounding contextual window around a detected brand or competitor mention."""

    matched_text: str = Field(
        ...,
        description="Exact matched entity string from the text.",
    )
    canonical_name: str = Field(
        ...,
        description="Canonical brand or competitor entity name.",
    )
    is_alias: bool = Field(
        default=False,
        description="Whether an alias was matched instead of the canonical brand name.",
    )
    start_char: int = Field(
        ...,
        description="Zero-indexed start character index in the raw response text.",
    )
    end_char: int = Field(
        ...,
        description="Zero-indexed end character index in the raw response text.",
    )
    context_window: str = Field(
        ...,
        description="Bounded surrounding sentence or paragraph context enclosing the mention.",
    )
    relative_position: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized position in text (0.0 = beginning, 1.0 = end of answer).",
    )


class CompetitorMention(BaseModel):
    """Observation data for a specific competitor within a response."""

    competitor_name: str = Field(
        ...,
        description="Name of the detected competitor brand.",
    )
    mentioned: bool = Field(
        ...,
        description="Whether the competitor was detected in the response.",
    )
    mention_count: int = Field(
        default=0,
        ge=0,
        description="Frequency count of competitor mentions.",
    )
    contexts: list[MentionContext] = Field(
        default_factory=list,
        description="Context snippets enclosing the competitor mentions.",
    )
    first_position: float | None = Field(
        default=None,
        description="Normalized position of the first competitor mention in the text (0.0 to 1.0).",
    )


class ResponseObservation(BaseModel):
    """Normalized analytical observation derived from one raw LLM response."""

    observation_id: str = Field(
        ...,
        description="Unique observation identifier, traceable to the parent response.",
    )
    audit_id: str = Field(
        ...,
        description="Parent audit identifier.",
    )
    response_id: str = Field(
        ...,
        description="Reference to the immutable RawLLMResponse this observation was derived from.",
    )
    prompt_id: str = Field(
        ...,
        description="Prompt ID evaluated.",
    )
    provider: str = Field(
        ...,
        description="Provider queried (e.g., 'openai', 'gemini').",
    )
    model: str = Field(
        ...,
        description="Model evaluated.",
    )
    topic: str = Field(
        default="general",
        description="Topic category inherited from prompt.",
    )

    # Brand Visibility Metrics
    brand: str = Field(
        ...,
        description="Target brand canonical name.",
    )
    brand_mentioned: bool = Field(
        ...,
        description="True if the target brand or any configured alias was mentioned.",
    )
    brand_mention_count: int = Field(
        default=0,
        ge=0,
        description="Total occurrence count of target brand and aliases.",
    )
    brand_contexts: list[MentionContext] = Field(
        default_factory=list,
        description="Context snippets for all target brand mentions.",
    )
    first_brand_position: float | None = Field(
        default=None,
        description="Normalized text position of first target brand mention.",
    )
    recommendation_class: RecommendationClass = Field(
        default=RecommendationClass.ABSENT,
        description="Classified recommendation stance.",
    )

    # Competitor Observations
    competitors_present: bool = Field(
        default=False,
        description="True if at least one configured competitor was mentioned.",
    )
    competitor_mentions: list[CompetitorMention] = Field(
        default_factory=list,
        description="Per-competitor breakdown of mentions and contexts.",
    )

    # Citations & Sources
    citation_status: CitationStatus = Field(
        default=CitationStatus.NOT_SUPPORTED_BY_PROVIDER,
        description="Explicit state of citation availability for this response.",
    )
    citations: list[CitationRecord] = Field(
        default_factory=list,
        description="Normalized citations linked to this response.",
    )

    # Traceability & Versioning
    analysis_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata capturing detector version, matching parameters, etc.",
    )
