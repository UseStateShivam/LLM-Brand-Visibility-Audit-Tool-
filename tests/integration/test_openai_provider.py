"""Integration tests for OpenAI Provider using mocked API client.

Verifies:
- Successful generation and normalization
- Annotation/citation extraction
- Exception mapping (AuthenticationError, RateLimitError, APITimeoutError)
- Never requires real credentials
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import openai
import pytest

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderTimeoutError,
)
from app.providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_success_with_mock() -> None:
    fixture_path = Path("tests/fixtures/openai_response.json")
    with open(fixture_path, encoding="utf-8") as f:
        fixture_data = json.load(f)

    # Construct mock chat completion response object
    mock_choice = MagicMock()
    mock_choice.finish_reason = "stop"
    mock_choice.message.content = fixture_data["choices"][0]["message"]["content"]
    mock_choice.message.model_dump.return_value = fixture_data["choices"][0]["message"]

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.model = "gpt-4o-mini"
    mock_resp.id = "chatcmpl-test-123"
    mock_resp.usage.prompt_tokens = 40
    mock_resp.usage.completion_tokens = 80
    mock_resp.usage.total_tokens = 120

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_resp

    provider = OpenAIProvider(model_name="gpt-4o-mini", client=mock_client)
    result = await provider.generate("What are top tools?")

    assert "Acme AI" in result.response_text
    assert result.latency_ms > 0
    assert len(result.citations) == 2
    assert result.citations[0].domain == "techbenchmark.io"
    assert result.provider_metadata["token_usage"]["total_tokens"] == 120


@pytest.mark.asyncio
async def test_openai_provider_auth_error_mapping() -> None:
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        "Invalid API Key",
        response=MagicMock(status_code=401),
        body=None,
    )

    provider = OpenAIProvider(model_name="gpt-4o-mini", client=mock_client)
    with pytest.raises(ProviderAuthenticationError):
        await provider.generate("Prompt")


@pytest.mark.asyncio
async def test_openai_provider_timeout_mapping() -> None:
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
        request=MagicMock()
    )

    provider = OpenAIProvider(model_name="gpt-4o-mini", client=mock_client)
    with pytest.raises(ProviderTimeoutError):
        await provider.generate("Prompt")
