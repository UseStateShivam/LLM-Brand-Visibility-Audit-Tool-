"""Prompt validator module.

Enforces validation rules on audit prompts:
- Non-empty, minimum length checks
- Injection variable syntax validation
- Duplicate prompt text detection
- Topic sanity checks
"""

import re
from collections.abc import Sequence

from app.core.exceptions import ValidationError
from app.models.prompt import AuditPrompt


class PromptValidator:
    """Validates individual prompts and prompt collections."""

    # Matches {variable_name} placeholders
    VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    ALLOWED_VARIABLES = {"brand", "category", "industry", "competitor", "topic", "geography"}

    @classmethod
    def validate_prompt_text(cls, text: str) -> str:
        """Ensure prompt text is non-empty and of sufficient length."""
        if not text or not isinstance(text, str):
            raise ValidationError("Prompt text must be a non-empty string.")
        cleaned = text.strip()
        if len(cleaned) < 5:
            raise ValidationError(f"Prompt text is too short (min 5 chars): '{cleaned}'")
        return cleaned

    @classmethod
    def validate_template_variables(cls, template: str) -> set[str]:
        """Verify that any placeholders inside the template use permitted variable names."""
        found_vars = set(cls.VARIABLE_PATTERN.findall(template))
        disallowed = found_vars - cls.ALLOWED_VARIABLES
        if disallowed:
            raise ValidationError(
                f"Template contains disallowed variable placeholders: {disallowed}. "
                f"Allowed variables: {cls.ALLOWED_VARIABLES}"
            )
        return found_vars

    @classmethod
    def validate_prompt_collection(
        cls, prompts: Sequence[AuditPrompt]
    ) -> list[AuditPrompt]:
        """Validate a collection of AuditPrompt objects, rejecting duplicates.

        Args:
            prompts: Sequence of AuditPrompt models.

        Returns:
            Validated list of prompts.

        Raises:
            ValidationError: If prompt list is empty or contains duplicates.
        """
        if not prompts:
            raise ValidationError("An audit must contain at least one prompt.")

        seen_texts: set[str] = set()
        validated: list[AuditPrompt] = []

        for idx, prompt in enumerate(prompts):
            cleaned_text = cls.validate_prompt_text(prompt.text)
            normalized_key = cleaned_text.lower().strip()

            if normalized_key in seen_texts:
                raise ValidationError(
                    f"Duplicate prompt detected at index {idx}: '{cleaned_text}'"
                )
            seen_texts.add(normalized_key)
            validated.append(prompt)

        return validated
