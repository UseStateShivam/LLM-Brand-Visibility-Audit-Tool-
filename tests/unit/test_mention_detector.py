"""Unit tests for Brand Mention Detector.

Verifies:
- Exact brand name detection
- Alias detection
- Case-insensitivity
- Punctuation & whitespace normalization
- Rejection of substring false positives (e.g. 'Art' inside 'partial' or 'smart')
- Character span tracking and order
"""

from app.analysis.mention_detector import MentionDetector


def test_exact_brand_detection() -> None:
    detector = MentionDetector()
    text = "For customer automation, Acme AI is an outstanding platform."
    result = detector.detect(text, brand="Acme AI")

    assert result.mentioned is True
    assert result.mention_count == 1
    assert len(result.spans) == 1
    span = result.spans[0]
    assert span.canonical_name == "Acme AI"
    assert span.matched_text == "Acme AI"
    assert span.is_alias is False
    assert span.start_char == 25
    assert span.end_char == 32


def test_alias_detection() -> None:
    detector = MentionDetector()
    text = "We evaluated AcmeAI alongside legacy tools."
    result = detector.detect(text, brand="Acme", aliases=["AcmeAI"])

    assert result.mentioned is True
    assert result.mention_count == 1
    assert result.spans[0].matched_text == "AcmeAI"
    assert result.spans[0].is_alias is True


def test_case_insensitivity_and_curly_quotes() -> None:
    detector = MentionDetector()
    text = "Users love ‘acme ai’ for its speed."
    result = detector.detect(text, brand="Acme AI")

    assert result.mentioned is True
    assert result.mention_count == 1
    assert result.spans[0].matched_text.lower() == "acme ai"


def test_false_positive_substring_rejection() -> None:
    """Critical test: brand 'Art' must not match inside 'partial', 'smart', or 'article'."""
    detector = MentionDetector()
    text = "This is a partial evaluation of smart software tools in the article."
    result = detector.detect(text, brand="Art")

    assert result.mentioned is False
    assert result.mention_count == 0
    assert len(result.spans) == 0


def test_multiple_occurrences() -> None:
    detector = MentionDetector()
    text = "Acme AI is good. Later in the answer, Acme AI is mentioned again."
    result = detector.detect(text, brand="Acme AI")

    assert result.mentioned is True
    assert result.mention_count == 2
    assert result.spans[0].start_char < result.spans[1].start_char
    assert result.first_position is not None
    assert result.first_position == 0.0
