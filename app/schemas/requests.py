"""API request models for the FastAPI service.

Defines schemas and field validators for audit creation, execution, and prompt validation.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PromptCreateRequest(BaseModel):
    """Schema for supplying a prompt within an audit creation request."""

    text: str = Field(..., min_length=3, description="Verbatim prompt text to be submitted.")
    topic: str = Field(default="general", description="Topic category (e.g. 'solutions', 'pricing').")
    intent: str = Field(default="discovery", description="Intent category (e.g. 'discovery', 'comparison').")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom prompt metadata.")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Prompt text cannot be empty or whitespace only.")
        return clean


class ProviderConfigRequest(BaseModel):
    """Schema for selecting providers and models in an audit creation request."""

    provider: str = Field(..., description="Provider name ('openai' or 'gemini').")
    model: str | None = Field(default=None, description="Optional model identifier override.")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, gt=0)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("openai", "gemini"):
            raise ValueError(f"Unsupported provider '{v}'. Must be 'openai' or 'gemini'.")
        return clean


class AuditCreateRequest(BaseModel):
    """Schema for creating a new brand visibility audit."""

    brand: str = Field(..., min_length=1, description="Canonical target brand name (e.g. 'Acme AI').")
    aliases: list[str] = Field(default_factory=list, description="Alternative names, spellings, or acronyms.")
    brand_domain: str | None = Field(default=None, description="Domain name (e.g. 'acme.ai') for source attribution.")
    competitors: list[str] = Field(default_factory=list, description="List of competitor brand names to detect.")
    industry: str = Field(default="technology", description="Target industry or market category.")
    topics: list[str] = Field(default_factory=lambda: ["general"], description="List of topic categories.")
    prompts: list[PromptCreateRequest] = Field(..., min_length=1, description="Audit prompts to evaluate.")
    providers: list[ProviderConfigRequest] = Field(
        default_factory=lambda: [
            ProviderConfigRequest(provider="openai"),
            ProviderConfigRequest(provider="gemini"),
        ],
        min_length=1,
        description="Providers and models to query.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional client tags or run annotations.")

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Brand name cannot be blank.")
        return clean


class PromptPreviewRequest(BaseModel):
    """Schema for validating and previewing prompt variable substitution."""

    template: str = Field(..., min_length=3, description="Prompt template with variables like {brand}, {category}.")
    brand: str = Field(..., min_length=1)
    category: str = Field(default="")
    competitor: str | None = Field(default=None)
    topic: str = Field(default="general")
