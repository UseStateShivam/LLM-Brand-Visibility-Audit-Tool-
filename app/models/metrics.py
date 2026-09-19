"""Metrics and scoring domain models.

Defines the mathematical schemas for aggregate brand visibility metrics,
topic-level breakdowns, competitor presence rates, provider comparison metrics,
and visibility score cards.
"""

from typing import Any

from pydantic import BaseModel, Field


class TopicMetric(BaseModel):
    """Aggregate visibility metrics for a specific topic cluster."""

    topic: str
    total_prompts: int
    successful_responses: int
    brand_mentions: int
    mention_rate: float = Field(ge=0.0, le=1.0)
    recommendation_rate: float = Field(ge=0.0, le=1.0)
    competitor_presence_rate: float = Field(ge=0.0, le=1.0)


class ProviderMetric(BaseModel):
    """Aggregate visibility metrics broken down by LLM provider."""

    provider: str
    model: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    brand_mention_count: int
    mention_rate: float = Field(ge=0.0, le=1.0)
    recommendation_rate: float = Field(ge=0.0, le=1.0)
    average_latency_ms: float
    citations_supported: bool


class CompetitorSummaryMetric(BaseModel):
    """Summary of visibility performance for a single competitor."""

    competitor_name: str
    total_responses: int
    mentions_count: int
    mention_rate: float = Field(ge=0.0, le=1.0)
    head_to_head_wins: int = Field(
        default=0,
        description="Number of prompts where competitor appeared but target brand was absent.",
    )
    head_to_head_losses: int = Field(
        default=0,
        description="Number of prompts where target brand appeared but competitor was absent.",
    )
    co_occurrences: int = Field(
        default=0,
        description="Number of prompts where both target brand and competitor appeared.",
    )


class DomainFrequency(BaseModel):
    """Frequency count and share of citations from an observed domain."""

    domain: str
    citation_count: int
    is_brand_owned: bool
    percentage_of_all_citations: float = Field(ge=0.0, le=1.0)


class SourceAnalysisSummary(BaseModel):
    """Aggregate analysis of domains observed alongside LLM answers."""

    total_citations: int
    unique_domains_count: int
    brand_owned_citations: int
    third_party_citations: int
    top_domains: list[DomainFrequency] = Field(default_factory=list)
    citations_available_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of successful responses where citations were supported and available.",
    )


class OverallMetrics(BaseModel):
    """Master aggregate metrics calculated across the entire audit run."""

    total_prompts: int
    total_requests: int
    successful_responses: int
    failed_responses: int

    # Primary Audit Ratios
    mention_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="prompts_where_brand_mentioned / total_successful_responses",
    )
    recommendation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="prompts_where_brand_recommended / total_successful_responses",
    )
    citation_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="responses_with_brand_citations / responses_with_available_citations (None if unsupported)",
    )
    topic_coverage: float = Field(
        ge=0.0,
        le=1.0,
        description="topics_with_at_least_one_brand_mention / total_topics_audited",
    )
    competitor_presence_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="responses_with_any_competitor / total_successful_responses",
    )

    # Positional metric
    average_mention_position: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Average normalized text position of the first brand mention across all mentioned responses.",
    )

    # Transparent Composite Visibility Score (0 to 100)
    composite_visibility_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Transparent weighted score computed deterministically from transparent component ratios.",
    )
    score_formula_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Full documentation of weights and inputs used to compute composite_visibility_score.",
    )
