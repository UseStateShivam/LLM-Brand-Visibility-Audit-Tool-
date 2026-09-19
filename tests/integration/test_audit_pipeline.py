"""End-to-End Integration test for the full brand visibility audit pipeline.

Simulates the entire workflow from audit definition to final report and client summary:
1. Audit creation
2. Prompt dispatch against mocked OpenAI & Gemini providers
3. Raw response persistence
4. Analytical pipeline (mention detection, context, competitor, recommendation, citations)
5. Gap identification & ranking
6. Structured report generation & one-page summary validation
"""

from pathlib import Path

import pytest

from app.core.config import Settings
from app.models.audit import Audit, ProviderSelection
from app.models.prompt import AuditPrompt
from app.models.report import GapSeverity
from app.providers.base import LLMProvider, ProviderResult
from app.services.analysis_service import AnalysisService
from app.services.audit_service import AuditService
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.storage.json_store import JSONAuditStore


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for reproducible end-to-end integration tests."""

    def __init__(
        self,
        provider_name: str,
        response_text: str,
        citations=None,
    ) -> None:
        super().__init__(provider_name=provider_name, model_name=f"{provider_name}-mock")
        self._text = response_text
        self._citations = citations or []

    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> ProviderResult:
        return ProviderResult(
            response_text=self._text,
            latency_ms=45.0,
            citations=self._citations,
        )


@pytest.mark.asyncio
async def test_full_audit_pipeline_end_to_end(tmp_path: Path) -> None:
    # Use temporary directory for data storage during test
    test_settings = Settings(data_dir=tmp_path / "data")
    store = JSONAuditStore(test_settings)

    # 1. Prepare synthetic responses for OpenAI and Gemini
    # OpenAI response: Mentions both Acme AI and Competitor Beta AI
    openai_text = (
        "Here are the top tools for customer support automation:\n"
        "1. Beta AI: Outstanding enterprise routing.\n"
        "2. Acme AI: Highly recommended for rapid conversational support.\n"
    )
    # Gemini response: Mentions only Competitor Beta AI (Acme AI is absent -> Triggers Gap)
    gemini_text = (
        "The leading customer support tool is Beta AI. It dominates ticket management."
    )

    mock_openai = MockLLMProvider("openai", openai_text)
    mock_gemini = MockLLMProvider("gemini", gemini_text)

    # 2. Build audit services
    query_service = QueryService(settings=test_settings)
    analysis_service = AnalysisService(settings=test_settings)
    report_service = ReportService(settings=test_settings)
    audit_service = AuditService(
        store=store,
        query_service=query_service,
        analysis_service=analysis_service,
        report_service=report_service,
    )

    # 3. Create Audit
    audit = Audit(
        brand="Acme AI",
        aliases=["Acme"],
        competitors=["Beta AI"],
        industry="Support AI",
        topics=["automation"],
        prompts=[
            AuditPrompt(
                prompt_id="p_001",
                text="What are the best tools for customer support automation?",
                topic="automation",
            )
        ],
        providers=[
            ProviderSelection(provider="openai"),
            ProviderSelection(provider="gemini"),
        ],
    )
    created = audit_service.create_audit(audit)
    assert created.status.value == "CREATED"

    # 4. Execute Audit with mock providers
    report, raw_responses, observations = await audit_service.run_audit(
        created.audit_id,
        provider_instances=[mock_openai, mock_gemini],
    )

    # 5. Verify Raw Responses
    assert len(raw_responses) == 2
    assert all(r.success for r in raw_responses)
    saved_raws = store.get_raw_responses(created.audit_id)
    assert len(saved_raws) == 2

    # 6. Verify Observations
    assert len(observations) == 2
    obs_openai = next(o for o in observations if o.provider == "openai")
    obs_gemini = next(o for o in observations if o.provider == "gemini")

    # OpenAI observation: brand mentioned & recommended
    assert obs_openai.brand_mentioned is True
    assert obs_openai.recommendation_class.value in ("RECOMMENDED", "STRONGLY_RECOMMENDED")
    assert obs_openai.competitors_present is True

    # Gemini observation: brand absent & competitor present
    assert obs_gemini.brand_mentioned is False
    assert obs_gemini.competitors_present is True

    # 7. Verify Overall Metrics & Scoring
    metrics = report.overall_metrics
    assert metrics.total_prompts == 1
    assert metrics.successful_responses == 2
    assert metrics.mention_rate == 0.5  # 1 out of 2 responses mentioned Acme AI
    assert metrics.composite_visibility_score > 0

    # 8. Verify Gap Identification
    # Should identify Competitor Advantage Gap (Beta AI present when Acme absent in Gemini)
    assert len(report.visibility_gaps) >= 1
    comp_gap = next((g for g in report.visibility_gaps if g.gap_type == "COMPETITOR_PRESENCE_GAP"), None)
    assert comp_gap is not None
    assert comp_gap.severity == GapSeverity.CRITICAL
    assert "Beta AI" in comp_gap.competitors_involved

    # 9. Verify Ranked Observations
    assert len(report.ranked_observations) >= 1
    top_ranked = report.ranked_observations[0]
    assert top_ranked.rank == 1
    assert top_ranked.evidence_response_id is not None

    # 10. Verify Client Summary
    summary = report.client_summary
    assert summary.brand == "Acme AI"
    assert summary.mention_rate_percentage == 50.0
    assert len(summary.critical_visibility_gaps) >= 1
    assert len(summary.what_this_means) > 20
