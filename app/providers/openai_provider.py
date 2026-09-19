"""OpenAI LLM provider adapter.

Interfaces with the OpenAI Chat Completions API asynchronously.
Handles token telemetry, latency measurement, web search / source annotations
if present in provider metadata, and standard exception mapping.
"""

import time
from typing import Any
from urllib.parse import urlparse

import openai
from openai import AsyncOpenAI

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.models.citation import CitationRecord, CitationStatus
from app.providers.base import LLMProvider, ProviderResult


class OpenAIProvider(LLMProvider):
    """OpenAI API provider adapter."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        client: AsyncOpenAI | None = None,
    ) -> None:
        super().__init__(
            provider_name="openai",
            model_name=model_name,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        # Allow injecting a pre-configured or mocked AsyncOpenAI client for testing
        self._client = client or AsyncOpenAI(
            api_key=api_key or "placeholder_key",
            timeout=timeout_seconds,
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ProviderResult:
        """Execute chat completion request against OpenAI API."""
        start_time = time.perf_counter()

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            choice = response.choices[0]
            response_text = choice.message.content or ""

            # Extract provider telemetry
            provider_metadata: dict[str, Any] = {
                "finish_reason": choice.finish_reason,
                "model": response.model,
                "id": response.id,
            }
            if response.usage:
                provider_metadata["token_usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            # Check for structured citations/sources if present in annotations or tool calls
            citations: list[CitationRecord] = []
            citation_status = CitationStatus.NOT_SUPPORTED_BY_PROVIDER

            # If response contains message annotations (e.g. OpenAI Search / Assistants API)
            message_dict = choice.message.model_dump() if hasattr(choice.message, "model_dump") else {}
            annotations = message_dict.get("annotations", [])
            if annotations:
                citation_status = CitationStatus.AVAILABLE
                for idx, ann in enumerate(annotations):
                    if ann.get("type") == "url_citation":
                        url_data = ann.get("url_citation", {})
                        raw_url = url_data.get("url", "")
                        if raw_url:
                            domain = urlparse(raw_url).netloc.lower()
                            citations.append(
                                CitationRecord(
                                    url=raw_url,
                                    domain=domain,
                                    title=url_data.get("title"),
                                    order_index=idx,
                                )
                            )

            return ProviderResult(
                response_text=response_text,
                latency_ms=elapsed_ms,
                provider_metadata=provider_metadata,
                citations=citations,
                citation_status=citation_status,
            )

        except openai.AuthenticationError as exc:
            raise ProviderAuthenticationError(
                message=f"OpenAI Authentication Failed: {exc}",
                provider="openai",
                model=self.model_name,
                details={"error_type": type(exc).__name__},
            ) from exc

        except openai.RateLimitError as exc:
            raise ProviderRateLimitError(
                message=f"OpenAI Rate Limit Exceeded: {exc}",
                provider="openai",
                model=self.model_name,
                details={"error_type": type(exc).__name__},
            ) from exc

        except (openai.APITimeoutError, TimeoutError) as exc:
            raise ProviderTimeoutError(
                message=f"OpenAI Request Timed Out ({self.timeout_seconds}s): {exc}",
                provider="openai",
                model=self.model_name,
                details={"timeout_seconds": self.timeout_seconds},
            ) from exc

        except openai.APIError as exc:
            raise ProviderError(
                message=f"OpenAI API Error: {exc}",
                provider="openai",
                model=self.model_name,
                is_retryable=(exc.code in (500, 502, 503, 504)),
                status_code=exc.code if isinstance(exc.code, int) else None,
                details={"error_code": exc.code, "error_type": type(exc).__name__},
            ) from exc

        except Exception as exc:
            raise ProviderError(
                message=f"Unexpected failure calling OpenAI: {exc}",
                provider="openai",
                model=self.model_name,
                is_retryable=False,
                details={"error_type": type(exc).__name__},
            ) from exc
