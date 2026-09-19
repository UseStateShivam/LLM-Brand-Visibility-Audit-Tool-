"""Abstract base class and contract for LLM provider adapters.

Decouples the core auditing engine from specific LLM vendors (OpenAI, Gemini).
All provider adapters must normalize vendor outputs into standardized
`RawLLMResponse` and `CitationRecord` models.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.models.citation import CitationRecord, CitationStatus


class ProviderResult:
    """Normalized output container returned by an LLM provider invocation."""

    def __init__(
        self,
        response_text: str,
        latency_ms: float,
        provider_metadata: dict[str, Any] | None = None,
        citations: list[CitationRecord] | None = None,
        citation_status: CitationStatus = CitationStatus.NOT_SUPPORTED_BY_PROVIDER,
    ) -> None:
        self.response_text = response_text
        self.latency_ms = latency_ms
        self.provider_metadata = provider_metadata or {}
        self.citations = citations or []
        self.citation_status = citation_status


class LLMProvider(ABC):
    """Abstract Base Class defining the operational contract for an LLM provider adapter."""

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize provider adapter.

        Args:
            provider_name: Canonical identifier for the provider (e.g. 'openai', 'gemini').
            model_name: Model identifier (e.g. 'gpt-4o-mini', 'gemini-1.5-flash').
            api_key: Optional API key. If omitted, provider may attempt environment lookup.
            timeout_seconds: Network request timeout in seconds.
        """
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ProviderResult:
        """Submit a prompt to the LLM and return normalized response text and citations.

        Must handle provider-specific exceptions, translate them into domain
        `ProviderError` types, and measure wall-clock latency.

        Args:
            prompt: Verbatim prompt text.
            temperature: Sampling temperature (0.0 for deterministic audits).
            max_tokens: Maximum completion tokens.

        Returns:
            ProviderResult containing raw text, latency, citations, and metadata.

        Raises:
            ProviderTimeoutError: When provider request times out.
            ProviderRateLimitError: When rate limits/quotas are exceeded.
            ProviderAuthenticationError: When credentials are invalid.
            ProviderError: For unrecoverable provider failures.
        """
        raise NotImplementedError
