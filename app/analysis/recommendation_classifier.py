"""Recommendation classifier.

Determines the role and stance of the target brand in the model's answer:
- ABSENT: Target brand not mentioned at all.
- MENTIONED: Brand is referenced or acknowledged, but not explicitly advocated as a top solution.
- RECOMMENDED: Brand is included in a list of recommended tools/solutions or suggested for use.
- STRONGLY_RECOMMENDED: Brand is ranked #1, marked as the primary/top choice, or uniquely highlighted.

Uses deterministic, explainable linguistic and positional heuristics.
"""

import re

from app.models.observation import MentionContext, RecommendationClass


class RecommendationClassifier:
    """Classifies the recommendation degree of a brand mention within a response."""

    # Phrases indicating strong endorsement or top-tier ranking
    STRONG_ENDORSEMENT_PATTERNS = [
        re.compile(r"\b(?:top|number\s+one|#1|best\s+overall|leading|industry\s+standard|our\s+top\s+pick)\b", re.IGNORECASE),
        re.compile(r"\b(?:highly\s+recommend(?:ed|s|ing)?|unmatched|standout|premier|market\s+leader)\b", re.IGNORECASE),
        re.compile(r"^\s*(?:1\.|1\))\s+", re.MULTILINE),  # Ranked first in a numbered list
    ]

    # Phrases indicating positive recommendation or solution inclusion
    RECOMMENDATION_PATTERNS = [
        re.compile(r"\b(?:recommend(?:ed|s|ing|ation)?|suggest(?:ed|s|ing)?|ideal\s+for|great\s+option|top\s+choice|notable\s+tool|popular\s+solution)\b", re.IGNORECASE),
        re.compile(r"\b(?:excellent|well-suited|powerful|robust|reliable|worth\s+considering)\b", re.IGNORECASE),
        re.compile(r"^\s*(?:[\*\-\•]|\d+\.)\s+", re.MULTILINE),  # Bulleted or numbered list item
    ]

    # Phrases indicating cautionary, negative, or purely incidental references
    INCIDENTAL_OR_NEGATIVE_PATTERNS = [
        re.compile(r"\b(?:however|unlike|limitation|drawback|alternative\s+to|not\s+recommended|outdated|legacy)\b", re.IGNORECASE),
    ]

    def classify(
        self,
        full_text: str,
        brand_mentioned: bool,
        contexts: list[MentionContext],
        first_position: float | None,
    ) -> RecommendationClass:
        """Classify recommendation stance deterministically.

        Args:
            full_text: Verbatim LLM response text.
            brand_mentioned: Whether target brand was detected.
            contexts: MentionContext objects for the brand.
            first_position: Normalized character position of first mention (0.0 to 1.0).

        Returns:
            RecommendationClass enum value.
        """
        if not brand_mentioned or not contexts:
            return RecommendationClass.ABSENT

        combined_contexts = " ".join(c.context_window for c in contexts)

        # Check for strong recommendation indicators
        has_strong_endorsement = any(
            p.search(combined_contexts) for p in self.STRONG_ENDORSEMENT_PATTERNS
        )
        # If mentioned in first 20% of text and formatted in a list/heading
        is_early_top_mention = (
            first_position is not None
            and first_position <= 0.20
            and any(
                p.search(contexts[0].context_window)
                for p in [re.compile(r"^\s*1[\.\)]", re.MULTILINE), re.compile(r"\b(?:best|top)\b", re.IGNORECASE)]
            )
        )

        if has_strong_endorsement or is_early_top_mention:
            return RecommendationClass.STRONGLY_RECOMMENDED

        # Check for standard recommendation indicators
        has_recommendation = any(
            p.search(combined_contexts) for p in self.RECOMMENDATION_PATTERNS
        )

        # If answer is structured as recommendations and brand is listed
        is_list_item = any(
            bool(re.search(r"^\s*(?:[\*\-\•]|\d+\.)\s*", c.context_window, re.MULTILINE))
            for c in contexts
        )

        if has_recommendation or is_list_item:
            return RecommendationClass.RECOMMENDED

        # Otherwise brand was acknowledged/mentioned without clear affirmative endorsement
        return RecommendationClass.MENTIONED
