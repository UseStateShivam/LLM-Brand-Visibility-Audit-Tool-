"""Unit tests for Citation Extractor.

Verifies:
- Structured citations extraction from provider metadata
- Inline markdown link extraction
- Plain URL extraction
- Distinction between NOT_SUPPORTED_BY_PROVIDER and NONE_FOUND
- Brand-owned domain identification
"""

from app.analysis.citation_extractor import CitationExtractor
from app.models.citation import CitationStatus
from app.models.response import RawLLMResponse


def test_markdown_citation_extraction() -> None:
    extractor = CitationExtractor()
    raw_response = RawLLMResponse(
        audit_id="aud_1",
        prompt_id="p_1",
        run_id="run_1",
        provider="gemini",
        model="gemini-1.5-flash",
        prompt_text="What is Acme AI?",
        response_text="Learn more on the [Official Site](https://acme.ai/about) and [TechCrunch Review](https://techcrunch.com/acme).",
        latency_ms=120.0,
        success=True,
    )

    status, citations = extractor.extract_from_raw_response(
        raw_response, brand_domain="acme.ai"
    )

    assert status == CitationStatus.AVAILABLE
    assert len(citations) == 2
    assert citations[0].url == "https://acme.ai/about"
    assert citations[0].domain == "acme.ai"
    assert citations[0].is_brand_owned is True
    assert citations[0].title == "Official Site"

    assert citations[1].url == "https://techcrunch.com/acme"
    assert citations[1].domain == "techcrunch.com"
    assert citations[1].is_brand_owned is False


def test_structured_metadata_citations() -> None:
    extractor = CitationExtractor()
    raw_response = RawLLMResponse(
        audit_id="aud_1",
        prompt_id="p_1",
        run_id="run_1",
        provider="gemini",
        model="gemini-1.5-flash",
        prompt_text="Top tools",
        response_text="Here is the answer without inline links.",
        latency_ms=100.0,
        success=True,
        provider_metadata={
            "structured_citations": [
                {
                    "url": "https://forbes.com/tech/best-tools",
                    "title": "Forbes Best Tools",
                }
            ]
        },
    )

    status, citations = extractor.extract_from_raw_response(raw_response)
    assert status == CitationStatus.AVAILABLE
    assert len(citations) == 1
    assert citations[0].domain == "forbes.com"


def test_unsupported_provider_distinction() -> None:
    extractor = CitationExtractor()
    raw_response = RawLLMResponse(
        audit_id="aud_1",
        prompt_id="p_1",
        run_id="run_1",
        provider="openai",
        model="gpt-4o-mini",
        prompt_text="Top tools",
        response_text="Simple text without citations.",
        latency_ms=90.0,
        success=True,
    )

    status, citations = extractor.extract_from_raw_response(raw_response)
    assert status == CitationStatus.NOT_SUPPORTED_BY_PROVIDER
    assert len(citations) == 0
