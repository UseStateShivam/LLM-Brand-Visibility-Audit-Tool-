"""Prompt builder for constructing deterministic audit prompts.

Supports:
- Preserving verbatim user prompts
- Generating prompts from templates with explicit variable injection
  ({brand}, {category}, {competitor})
- Assigning deterministic prompt IDs and order indices
"""

import hashlib
from typing import Any

from app.models.prompt import AuditPrompt
from app.prompts.validator import PromptValidator


class PromptBuilder:
    """Constructs reproducible AuditPrompt models from raw text or templates."""

    def __init__(self, validator: PromptValidator | None = None) -> None:
        self.validator = validator or PromptValidator()

    @staticmethod
    def generate_prompt_id(text: str, topic: str, order: int) -> str:
        """Create a deterministic prompt ID based on text, topic, and sequence."""
        payload = f"{topic}:{order}:{text.strip().lower()}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        return f"p_{digest}"

    def build_from_text(
        self,
        text: str,
        topic: str = "general",
        intent: str = "discovery",
        order_index: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> AuditPrompt:
        """Construct an AuditPrompt from verbatim prompt text."""
        cleaned_text = self.validator.validate_prompt_text(text)
        prompt_id = self.generate_prompt_id(cleaned_text, topic, order_index)
        return AuditPrompt(
            prompt_id=prompt_id,
            text=cleaned_text,
            topic=topic.strip().lower() if topic else "general",
            intent=intent.strip().lower() if intent else "discovery",
            order_index=order_index,
            metadata=metadata or {},
        )

    def build_from_template(
        self,
        template: str,
        variables: dict[str, str],
        topic: str = "general",
        intent: str = "discovery",
        order_index: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> AuditPrompt:
        """Render a template with supplied variables and return an AuditPrompt."""
        self.validator.validate_template_variables(template)

        # Apply safe string substitution
        rendered = template
        for var_name, var_value in variables.items():
            rendered = rendered.replace(f"{{{var_name}}}", str(var_value).strip())

        cleaned_text = self.validator.validate_prompt_text(rendered)
        prompt_id = self.generate_prompt_id(cleaned_text, topic, order_index)

        meta = dict(metadata or {})
        meta["template_original"] = template
        meta["applied_variables"] = variables

        return AuditPrompt(
            prompt_id=prompt_id,
            text=cleaned_text,
            topic=topic.strip().lower() if topic else "general",
            intent=intent.strip().lower() if intent else "discovery",
            order_index=order_index,
            metadata=meta,
        )
