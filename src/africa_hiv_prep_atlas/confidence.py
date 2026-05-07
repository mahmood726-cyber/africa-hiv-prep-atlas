"""Confidence tiering rules for Layer-T and Layer-M extractions."""
from __future__ import annotations

from enum import Enum

LOW_FLAGS = frozenset({"ambiguous", "negation", "multi_match"})


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


REVIEW_REQUIRED: frozenset[Confidence] = frozenset({Confidence.MEDIUM, Confidence.LOW})


def classify_confidence(method: str, flags: tuple) -> Confidence:
    if any(f in LOW_FLAGS for f in flags):
        return Confidence.LOW
    if method == "llm":
        return Confidence.MEDIUM
    if method == "regex":
        return Confidence.HIGH
    return Confidence.LOW
