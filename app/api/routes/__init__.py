# app/api/routes/__init__.py
"""API Route Handlers."""

from app.api.routes.audits import router as audits_router
from app.api.routes.health import router as health_router
from app.api.routes.prompts import router as prompts_router
from app.api.routes.reports import router as reports_router

__all__ = [
    "audits_router",
    "health_router",
    "prompts_router",
    "reports_router",
]
