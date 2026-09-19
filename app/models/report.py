"""Audit report and client summary models.

Defines the final deliverable structures:
1. Machine-readable, evidence-backed ranked audit report.
2. Executive one-page client summary.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.models.metrics import (
    CompetitorSummaryMetric,
    OverallMetrics,
    ProviderMetric,
    SourceAnalysisSummary,
    TopicMetric,
)


class GapSeverity(StrEnum):
    """Categorized severity of a detected brand visibility gap."""

    CRITICAL = "CRITICAL"  # e.g., competitor present while target brand is completely absent
    HIGH = "HIGH"          # e.g., zero brand visibility across an entire key topic
    MEDIUM = "MEDIUM"      # e.g., brand mentioned but never recommended
    LOW = "LOW"            # e.g., provider inconsistency or missing citation link


class VisibilityGap(BaseModel):
    """Specific observable gap between brand presence and market/competitor expectations."""

    gap_id: str
    gap_type: str = Field(
        ...,
        description="Category: 'COMPETITOR_PRESENCE_GAP', 'TOPIC_INVISIBILITY_GAP', 'WEAK_RECOMMENDATION_GAP', 'PROVIDER_DISCREPANCY_GAP'.",
    )
    severity: GapSeverity
    title: str
    description: str
    affected_topic: str | None = None
    affected_provider: str | None = None
    competitors_involved: list[str] = Field(default_factory=list)
    evidence_response_ids: list[str] = Field(
        default_factory=list,
        description="Traceable references to raw response IDs proving this gap.",
    )


class RankedObservation(BaseModel):
    """Evidence-backed observation prioritized for strategic client review."""

    rank: int = Field(ge=1)
    priority_score: float = Field(
        ...,
        description="Deterministic priority score sorting the finding by impact.",
    )
    category: str
    headline: str
    prompt_text: str
    provider: str
    model: str
    brand_status: str
    competitors_observed: list[str] = Field(default_factory=list)
    evidence_response_id: str
    evidence_quote: str | None = None
    rationale: str


class ClientSummary(BaseModel):
    """Compact, non-technical one-page executive summary for leadership & clients."""

    audit_id: str
    brand: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    providers_tested: list[str]
    total_prompts_tested: int

    # Executive Snapshot
    visibility_score: float
    mention_rate_percentage: float
    recommendation_rate_percentage: float
    topic_coverage_percentage: float
    citation_coverage_note: str

    # Key Strategic Findings
    top_strengths: list[str]
    critical_visibility_gaps: list[str]
    competitor_highlights: list[str]
    source_attribution_patterns: list[str]

    # Objective Interpretation & Next Steps
    what_this_means: str = Field(
        ...,
        description="Strictly factual interpretation bounded by measured data; no exaggerated claims.",
    )
    recommended_investigation_areas: list[str]


class AuditReport(BaseModel):
    """Complete, auditable visibility report combining metrics, lineage, and ranked gaps."""

    report_id: str
    audit_id: str
    brand: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    analysis_version: str = "1.0"
    scoring_version: str = "1.0"

    # Core Metrics
    overall_metrics: OverallMetrics
    topic_breakdown: list[TopicMetric]
    provider_breakdown: list[ProviderMetric]
    competitor_observations: list[CompetitorSummaryMetric]
    source_analysis: SourceAnalysisSummary

    # Strategic Analysis & Gaps
    visibility_gaps: list[VisibilityGap]
    ranked_observations: list[RankedObservation]

    # Synthesized Summaries
    executive_summary: str
    client_summary: ClientSummary

    # Complete Audit Lineage
    metadata: dict[str, Any] = Field(default_factory=dict)
