"""FastAPI application initialization and lifecycle setup.

Configures:
- Application routers (/health, /audits, /prompts)
- Global exception handlers mapping domain errors to structured HTTP responses
- CORS middleware
- Structured logging startup
"""

from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.audits import router as audits_router
from app.api.routes.health import router as health_router
from app.api.routes.prompts import router as prompts_router
from app.api.routes.reports import router as reports_router
from app.core.config import get_settings
from app.core.exceptions import (
    AuditAppError,
    AuditNotFoundError,
    ReportUnavailableError,
    UnsupportedProviderError,
    ValidationError,
)
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    # Configure structured logging
    setup_logging(
        log_level=settings.log_level,
        json_format=(settings.app_env == "production"),
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A production-grade backend audit platform that measures brand visibility "
            "in LLM-generated answers, extracts citation and source attribution, detects "
            "visibility gaps, and generates client-ready ranked reports."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration for prospective dashboard integrations
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(health_router)
    app.include_router(audits_router)
    app.include_router(reports_router)
    app.include_router(prompts_router)

    # Global Domain Exception Handlers
    @app.exception_handler(AuditNotFoundError)
    async def handle_audit_not_found(
        request: Request, exc: AuditNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "AUDIT_NOT_FOUND",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    @app.exception_handler(ReportUnavailableError)
    async def handle_report_unavailable(
        request: Request, exc: ReportUnavailableError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "REPORT_UNAVAILABLE",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    @app.exception_handler(ValidationError)
    async def handle_validation_error(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    @app.exception_handler(UnsupportedProviderError)
    async def handle_unsupported_provider(
        request: Request, exc: UnsupportedProviderError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "UNSUPPORTED_PROVIDER",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    @app.exception_handler(AuditAppError)
    async def handle_generic_audit_error(
        request: Request, exc: AuditAppError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_AUDIT_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    return app


app = create_app()
