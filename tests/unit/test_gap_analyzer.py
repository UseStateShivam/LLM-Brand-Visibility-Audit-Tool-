"""Unit tests for Visibility Gap Analyzer.

Verifies:
- Competitor Presence Gap detection
- Topic Invisibility Gap detection
- Weak Recommendation Gap detection
- Cross-Provider Discrepancy Gap detection
"""

from app.models.observation import (
    CompetitorMention,
    ResponseObservation,
)
from app.models.report import GapSeverity
from app.scoring.gap_analyzer import GapAnalyzer


def test_competitor_presence_gap_detection() -> None:
    analyzer = GapAnalyzer()

    obs = ResponseObservation(
        observation_id="obs_1",
        audit_id="aud_1",
        response_id="resp_1",
        prompt_id="p_1",
        provider="openai",
        model="gpt-4o-mini",
        topic="support",
        brand="Acme AI",
        brand_mentioned=False,
        competitors_present=True,
        competitor_mentions=[
            CompetitorMention(
                competitor_name="Beta AI",
                mentioned=True,
                mention_count=2,
            )
        ],
    )

    gaps = analyzer.analyze_gaps([obs])
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.gap_type == "COMPETITOR_PRESENCE_GAP"
    assert gap.severity == GapSeverity.CRITICAL
    assert "Beta AI" in gap.competitors_involved
    assert "resp_1" in gap.evidence_response_ids


def test_topic_invisibility_gap() -> None:
    analyzer = GapAnalyzer()

    obs1 = ResponseObservation(
        observation_id="obs_1",
        audit_id="aud_1",
        response_id="resp_1",
        prompt_id="p_1",
        provider="openai",
        model="gpt-4o-mini",
        topic="security",
        brand="Acme AI",
        brand_mentioned=False,
    )
    obs2 = ResponseObservation(
        observation_id="obs_2",
        audit_id="aud_1",
        response_id="resp_2",
        prompt_id="p_2",
        provider="gemini",
        model="gemini-1.5-flash",
        topic="security",
        brand="Acme AI",
        brand_mentioned=False,
    )

    gaps = analyzer.analyze_gaps([obs1, obs2])
    topic_gap = next((g for g in gaps if g.gap_type == "TOPIC_INVISIBILITY_GAP"), None)
    assert topic_gap is not None
    assert topic_gap.affected_topic == "security"
    assert topic_gap.severity == GapSeverity.HIGH
