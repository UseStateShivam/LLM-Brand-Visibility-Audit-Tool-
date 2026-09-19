# app/models/__init__.py
"""Domain models for LLM Brand Visibility Audit Tool."""

from app.models.audit import Audit, AuditStatus, ProviderSelection
from app.models.citation import CitationRecord, CitationStatus
from app.models.metrics import (
    CompetitorSummaryMetric,
    DomainFrequency,
    OverallMetrics,
    ProviderMetric,
    SourceAnalysisSummary,
    TopicMetric,
)
from app.models.observation import (
    CompetitorMention,
    MentionContext,
    RecommendationClass,
    ResponseObservation,
)
from app.models.prompt import AuditPrompt
from app.models.report import (
    AuditReport,
    ClientSummary,
    GapSeverity,
    RankedObservation,
    VisibilityGap,
)
from app.models.response import RawLLMResponse

__all__ = [
    "Audit",
    "AuditPrompt",
    "AuditReport",
    "AuditStatus",
    "CitationRecord",
    "CitationStatus",
    "ClientSummary",
    "CompetitorMention",
    "CompetitorSummaryMetric",
    "DomainFrequency",
    "GapSeverity",
    "MentionContext",
    "OverallMetrics",
    "ProviderMetric",
    "ProviderSelection",
    "RankedObservation",
    "RawLLMResponse",
    "RecommendationClass",
    "ResponseObservation",
    "SourceAnalysisSummary",
    "TopicMetric",
    "VisibilityGap",
]
