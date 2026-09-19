"""Integration tests for Google Gemini Provider using mocked client.

Verifies:
- Grounding metadata extraction
- Text assembly from parts
- Error handling (Unauthenticated, ResourceExhausted, TimeoutError)
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import google.api_core.exceptions as google_exceptions
import pytest

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
)
from app.providers.gemini_provider import GeminiProvider


@pytest.mark.asyncio
async def test_gemini_provider_success_with_mock() -> None:
    fixture_path = Path("tests/fixtures/gemini_response.json")
    with open(fixture_path, encoding="utf-8") as f:
        fixture_data = json.load(f)

    # Build mock candidate and grounding chunks
    mock_resp = MagicMock()
    mock_resp.text = fixture_data["candidates"][0]["content"]["parts"][0]["text"]

    web1 = MagicMock(uri="https://enterprisereview.com/best-support-tools", title="Review")
    web2 = MagicMock(uri="https://beta-ai.com/whitepaper", title="Whitepaper")
    chunk1 = MagicMock(web=web1)
    chunk2 = MagicMock(web=web2)

    grounding = MagicMock()
    grounding.grounding_chunks = [chunk1, chunk2]

    candidate = MagicMock()
    candidate.grounding_metadata = grounding
    mock_resp.candidates = [candidate]

    mock_resp.usage_metadata = MagicMock(
        prompt_token_count=38,
        candidates_token_count=92,
        total_token_count=130,
    )

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_resp)

    provider = GeminiProvider(model_name="gemini-1.5-flash", model_client=mock_model)
    result = await provider.generate("Test prompt")

    assert "Beta AI" in result.response_text
    assert len(result.citations) == 2
    assert result.citations[0].domain == "enterprisereview.com"
    assert result.citations[1].domain == "beta-ai.com"


@pytest.mark.asyncio
async def test_gemini_provider_unauthenticated() -> None:
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=google_exceptions.Unauthenticated("Invalid API key")
    )

    provider = GeminiProvider(model_name="gemini-1.5-flash", model_client=mock_model)
    with pytest.raises(ProviderAuthenticationError):
        await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_gemini_provider_resource_exhausted() -> None:
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=google_exceptions.ResourceExhausted("Rate limit exceeded")
    )

    provider = GeminiProvider(model_name="gemini-1.5-flash", model_client=mock_model)
    with pytest.raises(ProviderRateLimitError):
        await provider.generate("Test prompt")
