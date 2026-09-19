"""Context extractor for brand and competitor mentions.

Captures bounded surrounding sentence and paragraph context around
detected character spans.
Answers the key audit question: "Why and in what framing did the model mention this entity?"
Preserves verbatim wording without paraphrasing or rewriting.
"""

import re

from app.analysis.mention_detector import MentionSpan
from app.models.observation import MentionContext


class ContextExtractor:
    """Extracts bounded linguistic context surrounding detected entity mentions."""

    def __init__(self, window_chars: int = 150) -> None:
        """Initialize extractor.

        Args:
            window_chars: Default fallback character window radius if sentence boundaries are absent.
        """
        self.window_chars = window_chars
        # Sentence splitting pattern (handles . ! ? followed by space or newline)
        self._sentence_regex = re.compile(r"(?<=[.!?])\s+")

    def extract_context(
        self,
        full_text: str,
        span: MentionSpan,
    ) -> MentionContext:
        """Extract a clean, readable context window enclosing a MentionSpan.

        Expands to natural sentence boundaries where possible; otherwise bounds
        by `window_chars` around the mention.
        """
        text_len = len(full_text)
        if text_len == 0:
            return MentionContext(
                matched_text=span.matched_text,
                canonical_name=span.canonical_name,
                is_alias=span.is_alias,
                start_char=span.start_char,
                end_char=span.end_char,
                context_window="",
                relative_position=span.relative_position,
            )

        # Look backward for beginning of sentence or paragraph
        start_bound = max(0, span.start_char - self.window_chars)
        before_text = full_text[start_bound : span.start_char]
        last_newline = before_text.rfind("\n")
        last_period = before_text.rfind(". ")

        best_left = max(last_newline, last_period)
        if best_left != -1:
            context_start = start_bound + best_left + 1
        else:
            context_start = start_bound

        # Look forward for end of sentence or paragraph
        end_bound = min(text_len, span.end_char + self.window_chars)
        after_text = full_text[span.end_char : end_bound]
        next_newline = after_text.find("\n")
        next_period = after_text.find(". ")

        candidates = [idx for idx in (next_newline, next_period) if idx != -1]
        if candidates:
            best_right = min(candidates)
            context_end = span.end_char + best_right + 1
        else:
            context_end = end_bound

        raw_window = full_text[context_start:context_end].strip()

        # Fallback if window is somehow too narrow
        if len(raw_window) < len(span.matched_text):
            raw_window = full_text[max(0, span.start_char - 40) : min(text_len, span.end_char + 40)].strip()

        return MentionContext(
            matched_text=span.matched_text,
            canonical_name=span.canonical_name,
            is_alias=span.is_alias,
            start_char=span.start_char,
            end_char=span.end_char,
            context_window=raw_window,
            relative_position=span.relative_position,
        )

    def extract_all(
        self,
        full_text: str,
        spans: list[MentionSpan],
    ) -> list[MentionContext]:
        """Extract context objects for a list of spans."""
        return [self.extract_context(full_text, span) for span in spans]
