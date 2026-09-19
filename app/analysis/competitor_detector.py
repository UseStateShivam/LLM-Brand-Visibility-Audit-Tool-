"""Competitor detector module.

Evaluates raw LLM responses against explicitly configured competitor entities.
Extracts mentions, counts, positions, and surrounding contexts using the same
robust, false-positive-resistant regex boundary rules.
"""

from app.analysis.context_extractor import ContextExtractor
from app.analysis.mention_detector import MentionDetector
from app.models.observation import CompetitorMention


class CompetitorDetector:
    """Detects and captures competitor mentions across LLM responses."""

    def __init__(
        self,
        mention_detector: MentionDetector | None = None,
        context_extractor: ContextExtractor | None = None,
    ) -> None:
        self.detector = mention_detector or MentionDetector()
        self.context_extractor = context_extractor or ContextExtractor()

    def detect_competitors(
        self,
        text: str,
        competitors: list[str],
    ) -> list[CompetitorMention]:
        """Detect all configured competitors in response text.

        Args:
            text: Raw LLM response text.
            competitors: List of competitor brand names.

        Returns:
            List of CompetitorMention records.
        """
        results: list[CompetitorMention] = []

        for competitor in competitors:
            clean_name = competitor.strip()
            if not clean_name:
                continue

            detection = self.detector.detect(text=text, brand=clean_name, aliases=[])
            contexts = self.context_extractor.extract_all(text, detection.spans)

            results.append(
                CompetitorMention(
                    competitor_name=clean_name,
                    mentioned=detection.mentioned,
                    mention_count=detection.mention_count,
                    contexts=contexts,
                    first_position=detection.first_position,
                )
            )

        return results
