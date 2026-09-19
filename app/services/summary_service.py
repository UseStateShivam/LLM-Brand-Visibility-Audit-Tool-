"""Summary service.

Synthesizes detailed audit findings, metrics, and visibility gaps into
a high-impact, non-technical one-page executive client summary.
Strictly adheres to measured facts; never fabricates marketing assertions.
"""

from app.models.audit import Audit
from app.models.metrics import (
    CompetitorSummaryMetric,
    OverallMetrics,
    SourceAnalysisSummary,
)
from app.models.report import ClientSummary, VisibilityGap


class SummaryService:
    """Generates concise, client-oriented executive summaries from audit results."""

    def generate_client_summary(
        self,
        audit: Audit,
        overall_metrics: OverallMetrics,
        competitor_metrics: list[CompetitorSummaryMetric],
        source_summary: SourceAnalysisSummary,
        gaps: list[VisibilityGap],
    ) -> ClientSummary:
        """Produce structured ClientSummary from calculated audit results."""
        providers_tested = list({p.provider for p in audit.providers})

        # 1. Strengths
        strengths: list[str] = []
        if overall_metrics.mention_rate >= 0.7:
            strengths.append(
                f"Strong overall mention rate: '{audit.brand}' was present in {int(overall_metrics.mention_rate * 100)}% of model answers."
            )
        elif overall_metrics.mention_rate >= 0.4:
            strengths.append(
                f"Moderate mention rate: '{audit.brand}' appeared in {int(overall_metrics.mention_rate * 100)}% of responses."
            )

        if overall_metrics.recommendation_rate >= 0.5:
            strengths.append(
                f"High endorsement rate: Recommended in {int(overall_metrics.recommendation_rate * 100)}% of evaluated queries."
            )

        if overall_metrics.topic_coverage >= 0.75:
            strengths.append(
                f"Broad category footprint: Brand present across {int(overall_metrics.topic_coverage * 100)}% of audited topics."
            )

        if not strengths:
            strengths.append(
                f"Baseline established: Audit completed across {len(audit.prompts)} prompts and {len(providers_tested)} LLM providers."
            )

        # 2. Critical Gaps
        critical_gaps: list[str] = []
        for g in gaps[:4]:
            critical_gaps.append(f"{g.title} — {g.description}")
        if not critical_gaps:
            critical_gaps.append("No critical competitor or topic visibility gaps observed.")

        # 3. Competitor Highlights
        comp_highlights: list[str] = []
        for c in competitor_metrics[:3]:
            if c.mentions_count > 0:
                comp_highlights.append(
                    f"'{c.competitor_name}': {int(c.mention_rate * 100)}% mention rate "
                    f"({c.head_to_head_wins} queries where target brand was absent)."
                )
        if not comp_highlights:
            comp_highlights.append("No competitor mentions detected in the audited queries.")

        # 4. Source Attribution Patterns
        source_patterns: list[str] = []
        if source_summary.total_citations > 0:
            top_3 = ", ".join(f"{d.domain} ({d.citation_count})" for d in source_summary.top_domains[:3])
            source_patterns.append(f"Top cited domains observed alongside answers: {top_3}")
            if source_summary.brand_owned_citations > 0:
                source_patterns.append(
                    f"Brand-owned domain ({audit.brand_domain or 'official site'}) was cited {source_summary.brand_owned_citations} time(s)."
                )
            else:
                source_patterns.append(
                    "Third-party domains dominated sources; no direct citations of the brand's official domain observed."
                )
        else:
            source_patterns.append(
                "No external citation or web search grounding metadata exposed by providers for this run."
            )

        # 5. Citation coverage note
        citation_coverage_note = (
            f"Grounding data available for {int(source_summary.citations_available_rate * 100)}% of responses. "
            f"Direct brand citation rate: {int((overall_metrics.citation_rate or 0.0) * 100)}%."
            if source_summary.citations_available_rate > 0
            else "Citations not supported by the evaluated model configurations."
        )

        # 6. Objective factual interpretation
        what_this_means = (
            f"Based on the {overall_metrics.successful_responses} successful LLM answers evaluated, "
            f"'{audit.brand}' achieved a composite visibility score of {overall_metrics.composite_visibility_score:.1f}/100. "
            f"The brand was mentioned in {int(overall_metrics.mention_rate * 100)}% of prompts, "
            f"and affirmatively recommended in {int(overall_metrics.recommendation_rate * 100)}% of answers. "
            f"Competitor presence was detected in {int(overall_metrics.competitor_presence_rate * 100)}% of responses."
        )

        # 7. Next Investigation Areas
        recommended_investigations: list[str] = []
        if gaps:
            top_gap = gaps[0]
            if top_gap.affected_topic:
                recommended_investigations.append(
                    f"Investigate content and digital footprint within topic '{top_gap.affected_topic}'."
                )
            if top_gap.competitors_involved:
                recommended_investigations.append(
                    f"Analyze competitor positioning for {', '.join(top_gap.competitors_involved)} on high-intent comparison queries."
                )
        if source_summary.top_domains:
            top_domain = source_summary.top_domains[0].domain
            recommended_investigations.append(
                f"Review coverage and editorial listings on prominent reference domain '{top_domain}'."
            )
        if not recommended_investigations:
            recommended_investigations.append("Expand prompt set to include granular long-tail buyer queries.")

        return ClientSummary(
            audit_id=audit.audit_id,
            brand=audit.brand,
            providers_tested=providers_tested,
            total_prompts_tested=len(audit.prompts),
            visibility_score=overall_metrics.composite_visibility_score,
            mention_rate_percentage=round(overall_metrics.mention_rate * 100, 1),
            recommendation_rate_percentage=round(overall_metrics.recommendation_rate * 100, 1),
            topic_coverage_percentage=round(overall_metrics.topic_coverage * 100, 1),
            citation_coverage_note=citation_coverage_note,
            top_strengths=strengths,
            critical_visibility_gaps=critical_gaps,
            competitor_highlights=comp_highlights,
            source_attribution_patterns=source_patterns,
            what_this_means=what_this_means,
            recommended_investigation_areas=recommended_investigations,
        )
