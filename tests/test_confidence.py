from africa_hiv_prep_atlas.confidence import (
    classify_confidence,
    Confidence,
    REVIEW_REQUIRED,
)


def test_high_for_locked_regex_match():
    assert classify_confidence(method="regex", flags=()) == Confidence.HIGH


def test_medium_for_llm_assisted():
    assert classify_confidence(method="llm", flags=()) == Confidence.MEDIUM


def test_low_for_ambiguous():
    assert classify_confidence(method="regex", flags=("ambiguous",)) == Confidence.LOW


def test_low_for_negation_flagged():
    assert classify_confidence(method="regex", flags=("negation",)) == Confidence.LOW


def test_low_for_multi_match():
    assert classify_confidence(method="regex", flags=("multi_match",)) == Confidence.LOW


def test_review_required_includes_medium_and_low():
    assert Confidence.MEDIUM in REVIEW_REQUIRED
    assert Confidence.LOW in REVIEW_REQUIRED
    assert Confidence.HIGH not in REVIEW_REQUIRED
