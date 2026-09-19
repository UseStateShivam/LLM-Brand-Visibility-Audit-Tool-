"""Provider factory for instantiating LLM provider adapters.

Encapsulates provider creation logic, model defaults, API credential injection,
and validation against supported provider names.
"""

from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import UnsupportedProviderError
from app.providers.base import LLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider


class ProviderFactory:
    """Factory responsible for instantiating LLM provider adapter instances."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def create(
        self,
        provider_name: str,
        model_name: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> LLMProvider:
        """Create and return a configured LLMProvider instance.

        Args:
            provider_name: Name of the provider ('openai', 'gemini').
            model_name: Model identifier (falls back to configured default).
            api_key: Optional API key override.
            timeout_seconds: Request timeout in seconds.
            kwargs: Auxiliary arguments (e.g. injected mock clients for testing).

        Returns:
            Configured LLMProvider instance.

        Raises:
            UnsupportedProviderError: If the provider name is unrecognized.
        """
        normalized_name = provider_name.strip().lower()
        timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.settings.request_timeout_seconds
        )

        if normalized_name == "openai":
            selected_model = model_name or self.settings.openai_model
            selected_key = api_key or self.settings.openai_api_key
            client = kwargs.get("client")
            return OpenAIProvider(
                model_name=selected_model,
                api_key=selected_key,
                timeout_seconds=timeout,
                client=client,
            )

        elif normalized_name == "gemini":
            selected_model = model_name or self.settings.gemini_model
            selected_key = api_key or self.settings.gemini_api_key
            model_client = kwargs.get("model_client")
            return GeminiProvider(
                model_name=selected_model,
                api_key=selected_key,
                timeout_seconds=timeout,
                model_client=model_client,
            )

        else:
            raise UnsupportedProviderError(
                message=f"Unsupported LLM provider: '{provider_name}'. Supported providers: ['openai', 'gemini']"
            )
