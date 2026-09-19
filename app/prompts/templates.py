"""Standardized prompt templates across audit categories.

Provides structured prompt definitions for:
- Discovery: open-ended recommendation requests
- Comparison: head-to-head alternative evaluation
- Category: top brands / tools operating in an industry
- Problem-Solution: addressing specific operational challenges
- Authority: recognized industry leaders and standards
"""

from typing import Any

DISCOVERY_TEMPLATES = [
    {
        "intent": "discovery",
        "template": "What are the best {category} solutions currently available?",
        "topic": "solutions",
    },
    {
        "intent": "discovery",
        "template": "Which top tools would you recommend for modern {category}?",
        "topic": "tools",
    },
    {
        "intent": "discovery",
        "template": "Can you recommend reliable {category} platforms for high-growth companies?",
        "topic": "platforms",
    },
]

COMPARISON_TEMPLATES = [
    {
        "intent": "comparison",
        "template": "What are the top alternatives to {competitor} in the {category} space?",
        "topic": "alternatives",
    },
    {
        "intent": "comparison",
        "template": "Compare the leading software providers for {category}.",
        "topic": "comparison",
    },
]

CATEGORY_TEMPLATES = [
    {
        "intent": "category",
        "template": "Who are the major market leaders and emerging innovators in {category}?",
        "topic": "market_leaders",
    },
    {
        "intent": "category",
        "template": "List the most recognized enterprise software products for {category}.",
        "topic": "enterprise",
    },
]

PROBLEM_SOLUTION_TEMPLATES = [
    {
        "intent": "problem_solution",
        "template": "How can companies solve problems in {category}, and which software tools help accomplish this?",
        "topic": "workflows",
    },
    {
        "intent": "problem_solution",
        "template": "What are the recommended tools for streamlining {category} operations?",
        "topic": "efficiency",
    },
]

AUTHORITY_TEMPLATES = [
    {
        "intent": "authority",
        "template": "Which brands or products are considered the gold standard for {category}?",
        "topic": "reputation",
    }
]

ALL_DEFAULT_TEMPLATES: list[dict[str, Any]] = (
    DISCOVERY_TEMPLATES
    + COMPARISON_TEMPLATES
    + CATEGORY_TEMPLATES
    + PROBLEM_SOLUTION_TEMPLATES
    + AUTHORITY_TEMPLATES
)
