"""FastAPI dependency injection module.

Provides reusable dependencies for settings, stores, providers, and services.
Ensures singletons are properly managed and test mocks can be easily injected.
"""

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.prompts.builder import PromptBuilder
from app.providers.factory import ProviderFactory
from app.services.analysis_service import AnalysisService
from app.services.audit_service import AuditService
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.services.summary_service import SummaryService
from app.storage.audit_store import AuditStore
from app.storage.json_store import JSONAuditStore


def get_audit_store(
    settings: Settings = Depends(get_settings),
) -> AuditStore:
    """Provide instance of the persistence store."""
    return JSONAuditStore(settings=settings)


def get_provider_factory(
    settings: Settings = Depends(get_settings),
) -> ProviderFactory:
    """Provide instance of the LLM provider factory."""
    return ProviderFactory(settings=settings)


def get_query_service(
    factory: ProviderFactory = Depends(get_provider_factory),
    settings: Settings = Depends(get_settings),
) -> QueryService:
    """Provide query service instance."""
    return QueryService(factory=factory, settings=settings)


def get_analysis_service(
    settings: Settings = Depends(get_settings),
) -> AnalysisService:
    """Provide analysis service instance."""
    return AnalysisService(settings=settings)


def get_summary_service() -> SummaryService:
    """Provide summary service instance."""
    return SummaryService()


def get_report_service(
    summary_service: SummaryService = Depends(get_summary_service),
    settings: Settings = Depends(get_settings),
) -> ReportService:
    """Provide report service instance."""
    return ReportService(summary_service=summary_service, settings=settings)


def get_audit_service(
    store: AuditStore = Depends(get_audit_store),
    query_service: QueryService = Depends(get_query_service),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    report_service: ReportService = Depends(get_report_service),
) -> AuditService:
    """Provide master audit service instance."""
    return AuditService(
        store=store,
        query_service=query_service,
        analysis_service=analysis_service,
        report_service=report_service,
    )


def get_prompt_builder() -> PromptBuilder:
    """Provide prompt builder instance."""
    return PromptBuilder()
