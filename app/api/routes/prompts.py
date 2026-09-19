"""Prompt template preview and validation route handlers.

Endpoints:
- POST /prompts/preview: Validate template syntax and preview rendered prompt text
- GET  /prompts/templates: List default pre-configured audit prompt templates
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_prompt_builder
from app.core.exceptions import ValidationError
from app.prompts.builder import PromptBuilder
from app.prompts.templates import ALL_DEFAULT_TEMPLATES
from app.schemas.requests import PromptPreviewRequest
from app.schemas.responses import PromptPreviewResponse

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.get(
    "/templates",
    response_model=list[dict[str, Any]],
    summary="List Prompt Templates",
    description="Returns pre-built audit templates categorized by discovery, comparison, category, and authority.",
)
async def list_prompt_templates() -> list[dict[str, Any]]:
    """Return available default prompt templates."""
    return ALL_DEFAULT_TEMPLATES


@router.post(
    "/preview",
    response_model=PromptPreviewResponse,
    summary="Preview Prompt Template",
    description="Validates variable placeholders and returns the rendered prompt string.",
)
async def preview_prompt(
    request: PromptPreviewRequest,
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
) -> PromptPreviewResponse:
    """Preview variable substitution on a prompt template."""
    variables: dict[str, str] = {
        "brand": request.brand,
        "category": request.category,
    }
    if request.competitor:
        variables["competitor"] = request.competitor

    try:
        prompt = prompt_builder.build_from_template(
            template=request.template,
            variables=variables,
            topic=request.topic,
        )
        return PromptPreviewResponse(
            original_template=request.template,
            rendered_prompt=prompt.text,
            variables_applied=variables,
            is_valid=True,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc
