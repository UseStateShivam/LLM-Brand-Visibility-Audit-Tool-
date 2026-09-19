"""Report service.

Assembles observations, calculated metrics, source analyses, detected gaps,
and ranked findings into a complete, immutable, evidence-backed `AuditReport`.
Preserves full data lineage from high-level metrics down to raw response IDs.
"""

import uuid

from app.analysis.source_analyzer import SourceAnalyzer
from app.core.config import Settings, get_settings
from app.models.audit import Audit
from app.models.observation import ResponseObservation
from app.models.report import AuditReport
from app.models.response import RawLLMResponse
from app.scoring.gap_analyzer import GapAnalyzer
from app.scoring.metrics import MetricsCalculator
from app.scoring.ranking import ObservationRanker
from app.scoring.visibility_score import VisibilityScorer
from app.services.summary_service import SummaryService


class ReportService:
    """Coordinates assembly of comprehensive audit reports and executive summaries."""

    def __init__(
        self,
        visibility_scorer: VisibilityScorer | None = None,
        gap_analyzer: GapAnalyzer | None = None,
        observation_ranker: ObservationRanker | None = None,
        source_analyzer: SourceAnalyzer | None = None,
        summary_service: SummaryService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.visibility_scorer = visibility_scorer or VisibilityScorer()
        self.gap_analyzer = gap_analyzer or GapAnalyzer()
        self.observation_ranker = observation_ranker or ObservationRanker()
        self.source_analyzer = source_analyzer or SourceAnalyzer()
        self.summary_service = summary_service or SummaryService()

    def generate_report(
        self,
        audit: Audit,
        raw_responses: list[RawLLMResponse],
        observations: list[ResponseObservation],
    ) -> AuditReport:
        """Construct a full AuditReport domain object from audit execution data."""
        # 1. Compute overall and granular metrics
        overall_metrics = self.visibility_scorer.build_overall_metrics(
            total_prompts=len(audit.prompts),
            raw_responses=raw_responses,
            observations=observations,
            total_topics_count=len(audit.topics),
        )

        topic_metrics = MetricsCalculator.calculate_topic_metrics(observations)
        provider_metrics = MetricsCalculator.calculate_provider_metrics(
            raw_responses=raw_responses,
            observations=observations,
        )
        competitor_metrics = MetricsCalculator.calculate_competitor_metrics(
            observations=observations,
            configured_competitors=audit.competitors,
        )

        # 2. Analyze source attribution patterns
        source_summary = self.source_analyzer.analyze_sources(
            observations=observations,
            brand_domain=audit.brand_domain,
        )

        # 3. Detect visibility gaps
        gaps = self.gap_analyzer.analyze_gaps(observations)

        # 4. Prioritize and rank observations
        prompts_lookup = {p.prompt_id: p.text for p in audit.prompts}
        ranked_obs = self.observation_ranker.rank_observations(
            observations=observations,
            prompts_by_id=prompts_lookup,
        )

        # 5. Build client summary
        client_summary = self.summary_service.generate_client_summary(
            audit=audit,
            overall_metrics=overall_metrics,
            competitor_metrics=competitor_metrics,
            source_summary=source_summary,
            gaps=gaps,
        )

        # 6. Synthesize executive summary paragraph
        exec_summary = (
            f"Visibility Audit for '{audit.brand}' in the {audit.industry} sector. "
            f"Evaluated across {len(audit.prompts)} prompts and {len(provider_metrics)} LLM provider(s). "
            f"Overall Visibility Score: {overall_metrics.composite_visibility_score:.1f}/100. "
            f"Brand Mention Rate: {int(overall_metrics.mention_rate * 100)}%. "
            f"Recommendation Rate: {int(overall_metrics.recommendation_rate * 100)}%. "
            f"Identified {len(gaps)} strategic visibility gap(s)."
        )

        report_id = f"rep_{uuid.uuid4().hex[:12]}"

        return AuditReport(
            report_id=report_id,
            audit_id=audit.audit_id,
            brand=audit.brand,
            analysis_version=self.settings.analysis_version,
            scoring_version=self.settings.scoring_version,
            overall_metrics=overall_metrics,
            topic_breakdown=topic_metrics,
            provider_breakdown=provider_metrics,
            competitor_observations=competitor_metrics,
            source_analysis=source_summary,
            visibility_gaps=gaps,
            ranked_observations=ranked_obs,
            executive_summary=exec_summary,
            client_summary=client_summary,
            metadata={
                "audit_name": audit.brand,
                "industry": audit.industry,
                "total_requests": len(raw_responses),
                "successful_responses": overall_metrics.successful_responses,
            },
        )
