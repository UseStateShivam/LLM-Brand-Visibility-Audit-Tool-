"""Brand mention detector.

Identifies occurrences of the target brand and any configured aliases
in raw LLM response text.
Enforces strict word boundary and punctuation normalization to prevent
false positives (e.g. brand 'Art' matching inside 'partial' or 'smart').
"""

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class MentionSpan:
    """Character span and matched surface form of an entity in text."""

    canonical_name: str
    matched_text: str
    is_alias: bool
    start_char: int
    end_char: int
    relative_position: float


@dataclass(frozen=True)
class MentionDetectionResult:
    """Consolidated outcome of running mention detection on a text document."""

    mentioned: bool
    mention_count: int
    spans: list[MentionSpan]
    first_position: float | None


class MentionDetector:
    """Detects exact and normalized mentions of brand names and aliases."""

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Apply Unicode NFKC normalization and standardize apostrophes/dashes."""
        if not text:
            return ""
        # Normalize Unicode representations
        normalized = unicodedata.normalize("NFKC", text)
        # Normalize curly quotes and dashes to standard ASCII
        normalized = (
            normalized.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("—", "-")
            .replace("–", "-")
        )
        return normalized

    @classmethod
    def _build_regex(cls, term: str) -> re.Pattern[str]:
        """Compile a robust boundary-aware regex pattern for an entity.

        Handles alphanumeric entities with strict word boundaries (\b),
        while safely escaping terms containing punctuation (e.g. 'Brand+').
        """
        escaped_term = re.escape(term.strip())
        # If term begins/ends with word character, anchor with \b to avoid substring false positives
        prefix_boundary = r"\b" if re.match(r"^\w", term.strip()) else r"(?:^|\s)"
        suffix_boundary = r"\b" if re.search(r"\w$", term.strip()) else r"(?:$|\s)"
        pattern = f"{prefix_boundary}{escaped_term}{suffix_boundary}"
        return re.compile(pattern, re.IGNORECASE)

    def detect(
        self,
        text: str,
        brand: str,
        aliases: list[str] | None = None,
    ) -> MentionDetectionResult:
        """Scan text for occurrences of brand name and aliases.

        Args:
            text: Raw LLM response text.
            brand: Canonical brand name (e.g. 'Acme AI').
            aliases: Optional list of alternate forms (e.g. ['Acme', 'AcmeAI']).

        Returns:
            MentionDetectionResult with spans, counts, and relative position.
        """
        if not text or not brand:
            return MentionDetectionResult(
                mentioned=False,
                mention_count=0,
                spans=[],
                first_position=None,
            )

        norm_text = self._normalize_text(text)
        text_len = len(norm_text)
        found_spans: list[MentionSpan] = []

        # 1. Check canonical brand name first
        clean_brand = self._normalize_text(brand).strip()
        brand_regex = self._build_regex(clean_brand)

        for match in brand_regex.finditer(norm_text):
            start, end = match.span()
            matched_str = norm_text[start:end].strip()
            rel_pos = start / text_len if text_len > 0 else 0.0
            found_spans.append(
                MentionSpan(
                    canonical_name=brand,
                    matched_text=matched_str,
                    is_alias=False,
                    start_char=start,
                    end_char=end,
                    relative_position=round(rel_pos, 4),
                )
            )

        # 2. Check aliases (avoiding overlapping spans already claimed)
        if aliases:
            for alias in aliases:
                clean_alias = self._normalize_text(alias).strip()
                if not clean_alias:
                    continue
                alias_regex = self._build_regex(clean_alias)
                for match in alias_regex.finditer(norm_text):
                    start, end = match.span()
                    # Check if this span overlaps with any existing span
                    overlaps = any(
                        not (end <= existing.start_char or start >= existing.end_char)
                        for existing in found_spans
                    )
                    if not overlaps:
                        matched_str = norm_text[start:end].strip()
                        rel_pos = start / text_len if text_len > 0 else 0.0
                        found_spans.append(
                            MentionSpan(
                                canonical_name=brand,
                                matched_text=matched_str,
                                is_alias=True,
                                start_char=start,
                                end_char=end,
                                relative_position=round(rel_pos, 4),
                            )
                        )

        # Sort spans strictly by start_char sequence
        found_spans.sort(key=lambda s: s.start_char)

        first_pos = found_spans[0].relative_position if found_spans else None
        return MentionDetectionResult(
            mentioned=len(found_spans) > 0,
            mention_count=len(found_spans),
            spans=found_spans,
            first_position=first_pos,
        )
