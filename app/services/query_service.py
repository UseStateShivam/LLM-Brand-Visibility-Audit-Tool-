"""Query execution service.

Orchestrates concurrent, bounded dispatch of audit prompts across LLM providers:
- Strict concurrency throttling via asyncio.Semaphore
- Exponential backoff retries for transient provider failures (timeouts, rate limits)
- Non-retryable error short-circuiting (authentication failure, invalid request)
- Individual prompt failure isolation (one failed request does not abort the audit)
- Guaranteed generation of immutable RawLLMResponse records for data lineage
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Sequence

from app.core.config import Settings, get_settings
from app.core.exceptions import ProviderError
from app.models.audit import Audit, ProviderSelection
from app.models.prompt import AuditPrompt
from app.models.response import RawLLMResponse
from app.providers.base import LLMProvider, ProviderResult
from app.providers.factory import ProviderFactory

logger = logging.getLogger(__name__)


class QueryService:
    """Executes prompt batches across LLM providers with bounded concurrency and resilience."""

    def __init__(
        self,
        factory: ProviderFactory | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.factory = factory or ProviderFactory(self.settings)

    async def _execute_with_retry(
        self,
        provider: LLMProvider,
        prompt_text: str,
        temperature: float,
        max_tokens: int,
    ) -> ProviderResult:
        """Invoke provider.generate with bounded exponential backoff on retryable errors."""
        max_retries = self.settings.max_retries
        delay = self.settings.retry_initial_delay_seconds
        backoff = self.settings.retry_backoff_factor

        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await provider.generate(
                    prompt=prompt_text,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except ProviderError as exc:
                last_exception = exc
                if not exc.is_retryable or attempt == max_retries:
                    raise exc

                logger.warning(
                    f"Retryable error from provider '{provider.provider_name}' "
                    f"(attempt {attempt + 1}/{max_retries + 1}): {exc.message}. "
                    f"Backing off for {delay:.2f}s."
                )
                await asyncio.sleep(delay)
                delay *= backoff

            except Exception as exc:
                # Unknown exceptions are not retried to avoid infinite loops on syntax/logic bugs
                last_exception = exc
                raise exc

        # Safety fallback
        raise last_exception or ProviderError(
            "Max retries exhausted without response.",
            provider=provider.provider_name,
        )

    async def _query_single_prompt(
        self,
        semaphore: asyncio.Semaphore,
        provider: LLMProvider,
        prompt: AuditPrompt,
        audit_id: str,
        run_id: str,
        temperature: float,
        max_tokens: int,
    ) -> RawLLMResponse:
        """Execute a single prompt query against a provider protected by semaphore concurrency."""
        response_id = f"resp_{uuid.uuid4().hex[:12]}"
        start_perf = time.perf_counter()

        async with semaphore:
            logger.info(
                f"Querying [{provider.provider_name}:{provider.model_name}] "
                f"for prompt '{prompt.prompt_id}' in audit '{audit_id}'"
            )
            try:
                result = await self._execute_with_retry(
                    provider=provider,
                    prompt_text=prompt.text,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                meta = dict(result.provider_metadata)
                if result.citations:
                    meta["structured_citations"] = [
                        c.model_dump() for c in result.citations
                    ]

                return RawLLMResponse(
                    response_id=response_id,
                    audit_id=audit_id,
                    prompt_id=prompt.prompt_id,
                    run_id=run_id,
                    provider=provider.provider_name,
                    model=provider.model_name,
                    prompt_text=prompt.text,
                    response_text=result.response_text,
                    latency_ms=round(result.latency_ms, 2),
                    success=True,
                    provider_metadata=meta,
                )

            except ProviderError as exc:
                elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
                logger.error(
                    f"Provider failure [{provider.provider_name}] for prompt '{prompt.prompt_id}': {exc.message}"
                )
                return RawLLMResponse(
                    response_id=response_id,
                    audit_id=audit_id,
                    prompt_id=prompt.prompt_id,
                    run_id=run_id,
                    provider=provider.provider_name,
                    model=provider.model_name,
                    prompt_text=prompt.text,
                    response_text="",
                    latency_ms=round(elapsed_ms, 2),
                    success=False,
                    error_message=exc.message,
                    error_category=type(exc).__name__,
                    provider_metadata=exc.details,
                )

            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
                logger.error(
                    f"Unexpected exception querying [{provider.provider_name}] for prompt '{prompt.prompt_id}': {exc}"
                )
                return RawLLMResponse(
                    response_id=response_id,
                    audit_id=audit_id,
                    prompt_id=prompt.prompt_id,
                    run_id=run_id,
                    provider=provider.provider_name,
                    model=provider.model_name,
                    prompt_text=prompt.text,
                    response_text="",
                    latency_ms=round(elapsed_ms, 2),
                    success=False,
                    error_message=str(exc),
                    error_category="UnexpectedError",
                )

    async def execute_audit_queries(
        self,
        audit: Audit,
        run_id: str,
        provider_instances: Sequence[LLMProvider] | None = None,
    ) -> list[RawLLMResponse]:
        """Dispatch all prompts across selected providers with bounded concurrency.

        Args:
            audit: Audit definition containing prompts and provider configurations.
            run_id: Unique run identifier.
            provider_instances: Optional pre-instantiated provider adapters (useful for mocking).

        Returns:
            List of RawLLMResponse records.
        """
        # Instantiate providers if not passed directly
        providers_to_use: list[tuple[LLMProvider, ProviderSelection]] = []
        if provider_instances:
            for p in provider_instances:
                cfg = next(
                    (c for c in audit.providers if c.provider.lower() == p.provider_name.lower()),
                    ProviderSelection(provider=p.provider_name, model=p.model_name),
                )
                providers_to_use.append((p, cfg))
        else:
            for sel in audit.providers:
                instance = self.factory.create(
                    provider_name=sel.provider,
                    model_name=sel.model,
                )
                providers_to_use.append((instance, sel))

        semaphore = asyncio.Semaphore(self.settings.max_concurrent_requests)
        tasks = []

        for prompt in audit.prompts:
            for provider, cfg in providers_to_use:
                tasks.append(
                    self._query_single_prompt(
                        semaphore=semaphore,
                        provider=provider,
                        prompt=prompt,
                        audit_id=audit.audit_id,
                        run_id=run_id,
                        temperature=cfg.temperature,
                        max_tokens=cfg.max_tokens,
                    )
                )

        logger.info(
            f"Dispatching {len(tasks)} total queries across {len(providers_to_use)} providers "
            f"for audit '{audit.audit_id}' (max concurrency: {self.settings.max_concurrent_requests})"
        )

        results: list[RawLLMResponse] = await asyncio.gather(*tasks)
        return results
