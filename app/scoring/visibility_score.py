"""Composite visibility scoring system.

Implements an explainable, deterministic 0-100 composite visibility score.
Strictly adheres to the specification:
"Do not create an unexplained black-box score. The scoring formula must be
documented in code and report metadata."

Formula Specification (Version 1.0):
- Mention Rate Weight: 35% (Base presence in LLM answer sets)
- Recommendation Rate Weight: 30% (Qualitative endorsement rate)
- Topic Coverage Weight: 20% (Breadth across domain categories)
- Head-to-Head Competitor Parity: 15% (Target presence relative to competitor presence)
Total: 100 points maximum.
"""

from typing import Any

from app.models.metrics import OverallMetrics
from app.models.observation import ResponseObservation
from app.models.response import RawLLMResponse
from app.scoring.metrics import MetricsCalculator


class VisibilityScorer:
    """Computes transparent, reproducible visibility scores."""

    SCORING_VERSION = "1.0"

    # Documented explicit component weights
    WEIGHT_MENTION_RATE = 0.35
    WEIGHT_RECOMMENDATION_RATE = 0.30
    WEIGHT_TOPIC_COVERAGE = 0.20
    WEIGHT_COMPETITOR_PARITY = 0.15

    @classmethod
    def compute_composite_score(
        cls,
        mention_rate: float,
        recommendation_rate: float,
        topic_coverage: float,
        competitor_presence_rate: float,
    ) -> tuple[float, dict[str, Any]]:
        """Calculate deterministic 0-100 visibility score and formula explanation.

        Args:
            mention_rate: 0.0 to 1.0
            recommendation_rate: 0.0 to 1.0
            topic_coverage: 0.0 to 1.0
            competitor_presence_rate: 0.0 to 1.0

        Returns:
            Tuple of (score_0_to_100, formula_metadata_dict).
        """
        # Parity factor: if competitors appear frequently, brand should ideally also appear
        # If no competitors were present in the audit, full parity credit is granted
        if competitor_presence_rate > 0:
            # Parity is ratio of brand mention rate to competitor presence rate, capped at 1.0
            parity_factor = min(1.0, mention_rate / max(0.01, competitor_presence_rate))
        else:
            parity_factor = 1.0

        mention_points = mention_rate * cls.WEIGHT_MENTION_RATE * 100.0
        rec_points = recommendation_rate * cls.WEIGHT_RECOMMENDATION_RATE * 100.0
        topic_points = topic_coverage * cls.WEIGHT_TOPIC_COVERAGE * 100.0
        parity_points = parity_factor * cls.WEIGHT_COMPETITOR_PARITY * 100.0

        total_score = round(
            mention_points + rec_points + topic_points + parity_points, 2
        )
        total_score = max(0.0, min(100.0, total_score))

        formula_metadata = {
            "scoring_version": cls.SCORING_VERSION,
            "weights": {
                "mention_rate": cls.WEIGHT_MENTION_RATE,
                "recommendation_rate": cls.WEIGHT_RECOMMENDATION_RATE,
                "topic_coverage": cls.WEIGHT_TOPIC_COVERAGE,
                "competitor_parity": cls.WEIGHT_COMPETITOR_PARITY,
            },
            "points_breakdown": {
                "mention_points": round(mention_points, 2),
                "recommendation_points": round(rec_points, 2),
                "topic_coverage_points": round(topic_points, 2),
                "competitor_parity_points": round(parity_points, 2),
            },
            "formula_description": (
                "Composite Score (0-100) = (mention_rate * 35) + (recommendation_rate * 30) + "
                "(topic_coverage * 20) + (competitor_parity * 15)"
            ),
        }

        return total_score, formula_metadata

    def build_overall_metrics(
        self,
        total_prompts: int,
        raw_responses: list[RawLLMResponse],
        observations: list[ResponseObservation],
        total_topics_count: int,
    ) -> OverallMetrics:
        """Calculate full OverallMetrics domain object including composite score."""
        (
            tot_p,
            tot_req,
            succ,
            fail,
            m_rate,
            r_rate,
            c_rate,
            t_cov,
            comp_rate,
            avg_pos,
        ) = MetricsCalculator.calculate_overall_metrics(
            total_prompts=total_prompts,
            raw_responses=raw_responses,
            observations=observations,
            total_topics_count=total_topics_count,
        )

        composite_score, formula_meta = self.compute_composite_score(
            mention_rate=m_rate,
            recommendation_rate=r_rate,
            topic_coverage=t_cov,
            competitor_presence_rate=comp_rate,
        )

        return OverallMetrics(
            total_prompts=tot_p,
            total_requests=tot_req,
            successful_responses=succ,
            failed_responses=fail,
            mention_rate=m_rate,
            recommendation_rate=r_rate,
            citation_rate=c_rate,
            topic_coverage=t_cov,
            competitor_presence_rate=comp_rate,
            average_mention_position=avg_pos,
            composite_visibility_score=composite_score,
            score_formula_metadata=formula_meta,
        )
