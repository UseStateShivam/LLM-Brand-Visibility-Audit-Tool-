"""Google Gemini LLM provider adapter.

Interfaces with the Google Gemini API (google-generativeai / REST) asynchronously.
Extracts grounding metadata, web search citations, attribution sources,
measures latency, and normalizes exceptions into domain ProviderError types.
"""

import asyncio
import time
from typing import Any
from urllib.parse import urlparse

import google.api_core.exceptions as google_exceptions
import google.generativeai as genai

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.models.citation import CitationRecord, CitationStatus
from app.providers.base import LLMProvider, ProviderResult


class GeminiProvider(LLMProvider):
    """Google Gemini API provider adapter."""

    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        model_client: Any = None,
    ) -> None:
        super().__init__(
            provider_name="gemini",
            model_name=model_name,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
        if api_key:
            genai.configure(api_key=api_key)

        # Allow dependency injection of a mock GenerativeModel for testing
        self._model = model_client or genai.GenerativeModel(model_name=self.model_name)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ProviderResult:
        """Execute generation request against Google Gemini API."""
        start_time = time.perf_counter()

        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        try:
            # Wrap async call with strict timeout enforcement
            response = await asyncio.wait_for(
                self._model.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                ),
                timeout=self.timeout_seconds,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            response_text = ""
            try:
                response_text = response.text or ""
            except Exception:
                # If content was blocked or empty, text accessor may raise
                if hasattr(response, "candidates") and response.candidates:
                    first_candidate = response.candidates[0]
                    if hasattr(first_candidate, "content") and first_candidate.content.parts:
                        response_text = "".join(
                            part.text for part in first_candidate.content.parts if hasattr(part, "text")
                        )

            provider_metadata: dict[str, Any] = {
                "model": self.model_name,
            }

            # Check for candidate details and usage metadata
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                provider_metadata["token_usage"] = {
                    "prompt_token_count": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "candidates_token_count": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_token_count": getattr(response.usage_metadata, "total_token_count", 0),
                }

            # Extract grounding metadata / citations
            citations: list[CitationRecord] = []
            citation_status = CitationStatus.NONE_FOUND

            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                grounding_metadata = getattr(candidate, "grounding_metadata", None)
                if grounding_metadata:
                    citation_status = CitationStatus.AVAILABLE
                    # Extract web search queries / grounding chunks
                    chunks = getattr(grounding_metadata, "grounding_chunks", [])
                    for idx, chunk in enumerate(chunks):
                        web_chunk = getattr(chunk, "web", None)
                        if web_chunk and getattr(web_chunk, "uri", None):
                            uri = web_chunk.uri
                            title = getattr(web_chunk, "title", None)
                            domain = urlparse(uri).netloc.lower()
                            citations.append(
                                CitationRecord(
                                    url=uri,
                                    domain=domain,
                                    title=title,
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

        except TimeoutError as exc:
            raise ProviderTimeoutError(
                message=f"Gemini Request Timed Out after {self.timeout_seconds}s",
                provider="gemini",
                model=self.model_name,
                details={"timeout_seconds": self.timeout_seconds},
            ) from exc

        except google_exceptions.Unauthenticated as exc:
            raise ProviderAuthenticationError(
                message=f"Gemini Authentication Failed: {exc}",
                provider="gemini",
                model=self.model_name,
                details={"error_type": type(exc).__name__},
            ) from exc

        except google_exceptions.ResourceExhausted as exc:
            raise ProviderRateLimitError(
                message=f"Gemini Rate Limit / Quota Exceeded: {exc}",
                provider="gemini",
                model=self.model_name,
                details={"error_type": type(exc).__name__},
            ) from exc

        except google_exceptions.GoogleAPICallError as exc:
            is_retryable = exc.code in (500, 503, 504)
            raise ProviderError(
                message=f"Gemini API Error: {exc}",
                provider="gemini",
                model=self.model_name,
                is_retryable=is_retryable,
                status_code=exc.code,
                details={"error_type": type(exc).__name__},
            ) from exc

        except Exception as exc:
            raise ProviderError(
                message=f"Unexpected failure calling Gemini: {exc}",
                provider="gemini",
                model=self.model_name,
                is_retryable=False,
                details={"error_type": type(exc).__name__},
            ) from exc
