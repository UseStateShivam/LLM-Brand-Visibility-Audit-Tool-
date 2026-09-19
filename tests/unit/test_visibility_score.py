"""Unit tests for Visibility Scoring logic.

Verifies:
- Deterministic 0-100 score bounds
- Transparent weight formulas
- Version metadata preservation
- Parity calculations
"""

from app.scoring.visibility_score import VisibilityScorer


def test_visibility_score_perfect() -> None:
    score, meta = VisibilityScorer.compute_composite_score(
        mention_rate=1.0,
        recommendation_rate=1.0,
        topic_coverage=1.0,
        competitor_presence_rate=1.0,
    )
    assert score == 100.0
    assert meta["scoring_version"] == "1.0"
    assert "formula_description" in meta


def test_visibility_score_zero() -> None:
    score, meta = VisibilityScorer.compute_composite_score(
        mention_rate=0.0,
        recommendation_rate=0.0,
        topic_coverage=0.0,
        competitor_presence_rate=1.0,
    )
    assert score == 0.0


def test_visibility_score_moderate() -> None:
    score, meta = VisibilityScorer.compute_composite_score(
        mention_rate=0.5,
        recommendation_rate=0.4,
        topic_coverage=0.6,
        competitor_presence_rate=0.5,
    )
    # Expected: (0.5 * 35) + (0.4 * 30) + (0.6 * 20) + (1.0 * 15) = 17.5 + 12 + 12 + 15 = 56.5
    assert score == 56.5
    assert meta["points_breakdown"]["mention_points"] == 17.5
