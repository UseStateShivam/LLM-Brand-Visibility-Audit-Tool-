"""Analysis service.

Coordinates the analytical pipeline that transforms raw provider responses
into normalized, auditable `ResponseObservation` models:
1. Target brand & alias detection
2. Linguistic context window extraction
3. Competitor entity detection
4. Recommendation stance classification
5. Citation & grounding source extraction
"""

import uuid

from app.analysis.citation_extractor import CitationExtractor
from app.analysis.competitor_detector import CompetitorDetector
from app.analysis.context_extractor import ContextExtractor
from app.analysis.mention_detector import MentionDetector
from app.analysis.recommendation_classifier import RecommendationClassifier
from app.core.config import Settings, get_settings
from app.models.audit import Audit
from app.models.observation import ResponseObservation
from app.models.response import RawLLMResponse


class AnalysisService:
    """Orchestrates transformation of raw LLM responses into normalized observations."""

    def __init__(
        self,
        mention_detector: MentionDetector | None = None,
        context_extractor: ContextExtractor | None = None,
        competitor_detector: CompetitorDetector | None = None,
        recommendation_classifier: RecommendationClassifier | None = None,
        citation_extractor: CitationExtractor | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.mention_detector = mention_detector or MentionDetector()
        self.context_extractor = context_extractor or ContextExtractor()
        self.competitor_detector = competitor_detector or CompetitorDetector(
            mention_detector=self.mention_detector,
            context_extractor=self.context_extractor,
        )
        self.recommendation_classifier = (
            recommendation_classifier or RecommendationClassifier()
        )
        self.citation_extractor = citation_extractor or CitationExtractor()

    def analyze_response(
        self,
        raw_response: RawLLMResponse,
        audit: Audit,
    ) -> ResponseObservation:
        """Analyze a single successful raw LLM response.

        Args:
            raw_response: Immutable raw provider response.
            audit: Audit definition containing brand, aliases, competitors, and domain.

        Returns:
            Fully populated ResponseObservation domain model.
        """
        prompt_model = next(
            (p for p in audit.prompts if p.prompt_id == raw_response.prompt_id),
            None,
        )
        topic = prompt_model.topic if prompt_model else "general"

        text = raw_response.response_text or ""

        # 1. Detect target brand and aliases
        brand_detection = self.mention_detector.detect(
            text=text,
            brand=audit.brand,
            aliases=audit.aliases,
        )

        # 2. Extract surrounding context for brand mentions
        brand_contexts = self.context_extractor.extract_all(
            full_text=text,
            spans=brand_detection.spans,
        )

        # 3. Detect competitors
        competitor_mentions = self.competitor_detector.detect_competitors(
            text=text,
            competitors=audit.competitors,
        )
        has_competitors = any(c.mentioned for c in competitor_mentions)

        # 4. Classify recommendation stance
        rec_class = self.recommendation_classifier.classify(
            full_text=text,
            brand_mentioned=brand_detection.mentioned,
            contexts=brand_contexts,
            first_position=brand_detection.first_position,
        )

        # 5. Extract citations / grounding sources
        citation_status, citations = self.citation_extractor.extract_from_raw_response(
            raw_response=raw_response,
            brand_domain=audit.brand_domain,
        )

        obs_id = f"obs_{uuid.uuid4().hex[:12]}"

        return ResponseObservation(
            observation_id=obs_id,
            audit_id=audit.audit_id,
            response_id=raw_response.response_id,
            prompt_id=raw_response.prompt_id,
            provider=raw_response.provider,
            model=raw_response.model,
            topic=topic,
            brand=audit.brand,
            brand_mentioned=brand_detection.mentioned,
            brand_mention_count=brand_detection.mention_count,
            brand_contexts=brand_contexts,
            first_brand_position=brand_detection.first_position,
            recommendation_class=rec_class,
            competitors_present=has_competitors,
            competitor_mentions=competitor_mentions,
            citation_status=citation_status,
            citations=citations,
            analysis_metadata={
                "analysis_version": self.settings.analysis_version,
                "detector_method": "normalized_boundary_exact_match",
            },
        )

    def analyze_all(
        self,
        raw_responses: list[RawLLMResponse],
        audit: Audit,
    ) -> list[ResponseObservation]:
        """Transform all successful raw responses into observations."""
        observations: list[ResponseObservation] = []
        for r in raw_responses:
            if r.success:
                observations.append(self.analyze_response(r, audit))
        return observations
