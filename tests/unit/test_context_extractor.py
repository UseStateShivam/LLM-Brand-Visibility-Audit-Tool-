"""Unit tests for Context Extractor.

Verifies:
- Sentence boundary expansion
- Accurate preservation of surrounding text
- Non-paraphrasing guarantees
"""

from app.analysis.context_extractor import ContextExtractor
from app.analysis.mention_detector import MentionDetector


def test_context_window_extraction() -> None:
    detector = MentionDetector()
    extractor = ContextExtractor(window_chars=60)

    text = (
        "Enterprise support needs automation. "
        "Acme AI provides the fastest ticket resolution in this tier. "
        "Other platforms lag behind."
    )

    detection = detector.detect(text, brand="Acme AI")
    assert detection.mentioned is True

    contexts = extractor.extract_all(text, detection.spans)
    assert len(contexts) == 1
    ctx = contexts[0]
    assert ctx.matched_text == "Acme AI"
    assert "Acme AI provides the fastest ticket resolution in this tier." in ctx.context_window
    assert ctx.canonical_name == "Acme AI"
