"""Report and client summary retrieval route handlers.

Endpoints:
- GET /audits/{audit_id}/report: Returns the complete, evidence-backed AuditReport
- GET /audits/{audit_id}/report/summary: Returns the concise, one-page ClientSummary
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_service
from app.core.exceptions import AuditNotFoundError, ReportUnavailableError
from app.models.report import AuditReport, ClientSummary
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audits", tags=["Reports"])


@router.get(
    "/{audit_id}/report",
    response_model=AuditReport,
    summary="Get Full Audit Report",
    description=(
        "Returns the complete structured visibility audit report including overall metrics, "
        "topic breakdowns, competitor analysis, source attribution, visibility gaps, and ranked observations."
    ),
)
async def get_report(
    audit_id: str,
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditReport:
    """Retrieve full audit report."""
    try:
        return audit_service.get_report(audit_id)
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except ReportUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc


@router.get(
    "/{audit_id}/report/summary",
    response_model=ClientSummary,
    summary="Get One-Page Client Summary",
    description="Returns the compact, non-technical executive summary tailored for leadership and clients.",
)
async def get_summary(
    audit_id: str,
    audit_service: AuditService = Depends(get_audit_service),
) -> ClientSummary:
    """Retrieve concise one-page client summary."""
    try:
        return audit_service.get_summary(audit_id)
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except ReportUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
