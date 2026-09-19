"""Unit tests for Prompt Builder and Validator.

Verifies:
- Building from raw text
- Building from templates with variables
- Deterministic ID generation
- Validation rejection of empty text and duplicate prompts
"""

import pytest

from app.core.exceptions import ValidationError
from app.prompts.builder import PromptBuilder
from app.prompts.validator import PromptValidator


def test_prompt_build_from_text() -> None:
    builder = PromptBuilder()
    prompt = builder.build_from_text(
        text="What are the top AI customer support platforms?",
        topic="support",
        intent="discovery",
    )
    assert prompt.text == "What are the top AI customer support platforms?"
    assert prompt.topic == "support"
    assert prompt.prompt_id.startswith("p_")


def test_prompt_build_from_template() -> None:
    builder = PromptBuilder()
    template = "Compare {brand} against leading tools in {category}."
    variables = {"brand": "Acme AI", "category": "automation"}
    prompt = builder.build_from_template(template, variables=variables)

    assert prompt.text == "Compare Acme AI against leading tools in automation."
    assert prompt.metadata["applied_variables"]["brand"] == "Acme AI"


def test_validator_rejects_empty_or_too_short() -> None:
    validator = PromptValidator()
    with pytest.raises(ValidationError):
        validator.validate_prompt_text("   ")

    with pytest.raises(ValidationError):
        validator.validate_prompt_text("hi")


def test_validator_rejects_duplicate_prompts() -> None:
    builder = PromptBuilder()
    validator = PromptValidator()

    p1 = builder.build_from_text("What are the best tools for customer support?", order_index=0)
    p2 = builder.build_from_text("What are the best tools for customer support?", order_index=1)

    with pytest.raises(ValidationError):
        validator.validate_prompt_collection([p1, p2])
