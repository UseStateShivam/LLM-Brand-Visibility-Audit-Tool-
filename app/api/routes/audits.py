"""Audit management and execution route handlers.

Endpoints:
- POST /audits: Create an audit definition
- GET  /audits: List all audits
- GET  /audits/{audit_id}: Retrieve audit status and metadata
- POST /audits/{audit_id}/run: Run audit against configured LLM providers
- GET  /audits/{audit_id}/responses: Retrieve raw, immutable LLM responses
- GET  /audits/{audit_id}/observations: Retrieve normalized analytical observations
"""

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_service, get_prompt_builder
from app.core.exceptions import AuditNotFoundError
from app.models.audit import Audit, ProviderSelection
from app.prompts.builder import PromptBuilder
from app.schemas.requests import AuditCreateRequest
from app.schemas.responses import (
    AuditCreateResponse,
    AuditRunResponse,
    AuditStatusResponse,
    ObservationsListResponse,
    RawResponsesListResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audits", tags=["Audits"])


@router.post(
    "",
    response_model=AuditCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audit",
    description="Configures and persists a new brand visibility audit definition.",
)
async def create_audit(
    request: AuditCreateRequest,
    audit_service: AuditService = Depends(get_audit_service),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
) -> AuditCreateResponse:
    """Create a new audit definition."""
    # Build prompt models
    prompts = [
        prompt_builder.build_from_text(
            text=p.text,
            topic=p.topic,
            intent=p.intent,
            order_index=idx,
            metadata=p.metadata,
        )
        for idx, p in enumerate(request.prompts)
    ]

    # Build provider selection models
    providers = [
        ProviderSelection(
            provider=p.provider,
            model=p.model,
            temperature=p.temperature,
            max_tokens=p.max_tokens,
        )
        for p in request.providers
    ]

    audit = Audit(
        brand=request.brand,
        aliases=request.aliases,
        brand_domain=request.brand_domain,
        competitors=request.competitors,
        industry=request.industry,
        topics=request.topics,
        prompts=prompts,
        providers=providers,
        metadata=request.metadata,
    )

    created = audit_service.create_audit(audit)

    return AuditCreateResponse(
        audit_id=created.audit_id,
        brand=created.brand,
        status=created.status,
        total_prompts=len(created.prompts),
        providers=[p.provider for p in created.providers],
        created_at=created.created_at,
        message="Audit definition created successfully.",
    )


@router.get(
    "/{audit_id}",
    response_model=AuditStatusResponse,
    summary="Get Audit Status",
    description="Retrieve the current status, configurations, and metadata of an audit.",
)
async def get_audit(
    audit_id: str,
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditStatusResponse:
    """Retrieve audit details."""
    try:
        audit = audit_service.get_audit(audit_id)
        return AuditStatusResponse(
            audit_id=audit.audit_id,
            brand=audit.brand,
            status=audit.status,
            total_prompts=len(audit.prompts),
            providers=[p.model_dump() for p in audit.providers],
            created_at=audit.created_at,
            updated_at=audit.updated_at,
        )
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.post(
    "/{audit_id}/run",
    response_model=AuditRunResponse,
    summary="Run Audit",
    description="Executes prompt querying across configured LLM providers, performs analysis, and builds the report.",
)
async def run_audit(
    audit_id: str,
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditRunResponse:
    """Execute audit queries and analysis."""
    start_time = datetime.now(UTC)
    perf_start = time.perf_counter()

    try:
        report, raw_responses, _ = await audit_service.run_audit(audit_id)
        elapsed = round(time.perf_counter() - perf_start, 2)
        end_time = datetime.now(UTC)

        successful = sum(1 for r in raw_responses if r.success)
        failed = len(raw_responses) - successful

        return AuditRunResponse(
            audit_id=audit_id,
            run_id=report.report_id,
            status=audit_service.get_audit(audit_id).status,
            total_requests=len(raw_responses),
            successful_responses=successful,
            failed_responses=failed,
            started_at=start_time,
            completed_at=end_time,
            elapsed_seconds=elapsed,
            message=(
                f"Audit executed. {successful}/{len(raw_responses)} requests succeeded. "
                f"Report '{report.report_id}' is ready."
            ),
        )
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit execution encountered an unexpected error: {exc}",
        ) from exc


@router.get(
    "/{audit_id}/responses",
    response_model=RawResponsesListResponse,
    summary="Get Raw Responses",
    description="Retrieve all immutable raw LLM responses captured during the audit execution.",
)
async def get_raw_responses(
    audit_id: str,
    audit_service: AuditService = Depends(get_audit_service),
) -> RawResponsesListResponse:
    """Retrieve raw provider responses for audit verification."""
    try:
        responses = audit_service.get_raw_responses(audit_id)
        return RawResponsesListResponse(
            audit_id=audit_id,
            count=len(responses),
            responses=responses,
        )
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.get(
    "/{audit_id}/observations",
    response_model=ObservationsListResponse,
    summary="Get Observations",
    description="Retrieve normalized analytical observations derived from the raw responses.",
)
async def get_observations(
    audit_id: str,
    audit_service: AuditService = Depends(get_audit_service),
) -> ObservationsListResponse:
    """Retrieve normalized analytical observations."""
    try:
        observations = audit_service.get_observations(audit_id)
        return ObservationsListResponse(
            audit_id=audit_id,
            count=len(observations),
            observations=observations,
        )
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
