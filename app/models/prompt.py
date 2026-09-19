"""Prompt domain model.

Represents an individual brand audit prompt, its associated topic categorization,
intent, and optional configuration metadata.
"""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class AuditPrompt(BaseModel):
    """Domain model for an audit prompt to be dispatched to LLM providers."""

    prompt_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique deterministic or randomly assigned identifier for this prompt.",
    )
    text: str = Field(
        ...,
        min_length=3,
        description="The verbatim prompt text sent to the LLM.",
    )
    topic: str = Field(
        default="general",
        description="The topic, category, or domain cluster this prompt belongs to.",
    )
    intent: str = Field(
        default="discovery",
        description="The prompt intent classification (e.g. discovery, comparison, problem_solution, authority).",
    )
    order_index: int = Field(
        default=0,
        description="Explicit sequence ordering for reproducibility in multi-turn or batched runs.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional auxiliary attributes (e.g., target geography, persona framing).",
    )
