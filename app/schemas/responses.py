"""API response models for the FastAPI service.

Defines schemas for audit responses, run statuses, health endpoints, and error messages.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.audit import AuditStatus
from app.models.observation import ResponseObservation
from app.models.response import RawLLMResponse


class HealthResponse(BaseModel):
    """Schema returned by GET /health."""

    status: str = "ok"
    app_name: str
    version: str
    environment: str
    timestamp: datetime


class AuditCreateResponse(BaseModel):
    """Schema returned by POST /audits."""

    audit_id: str
    brand: str
    status: AuditStatus
    total_prompts: int
    providers: list[str]
    created_at: datetime
    message: str = "Audit successfully created."


class AuditRunResponse(BaseModel):
    """Schema returned by POST /audits/{audit_id}/run."""

    audit_id: str
    run_id: str
    status: AuditStatus
    total_requests: int
    successful_responses: int
    failed_responses: int
    started_at: datetime
    completed_at: datetime
    elapsed_seconds: float
    message: str


class AuditStatusResponse(BaseModel):
    """Schema returned by GET /audits/{audit_id}."""

    audit_id: str
    brand: str
    status: AuditStatus
    total_prompts: int
    providers: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class RawResponsesListResponse(BaseModel):
    """Schema returned by GET /audits/{audit_id}/responses."""

    audit_id: str
    count: int
    responses: list[RawLLMResponse]


class ObservationsListResponse(BaseModel):
    """Schema returned by GET /audits/{audit_id}/observations."""

    audit_id: str
    count: int
    observations: list[ResponseObservation]


class PromptPreviewResponse(BaseModel):
    """Schema returned by POST /prompts/preview."""

    original_template: str
    rendered_prompt: str
    variables_applied: dict[str, str]
    is_valid: bool


class ErrorResponse(BaseModel):
    """Standardized error envelope returned across all non-2xx responses."""

    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
