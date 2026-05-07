"""Country-level enrolment extraction with DossierGap negation guard."""
from __future__ import annotations

import re
from dataclasses import dataclass

from africa_hiv_prep_atlas.countries import AFRICAN_COUNTRIES, normalise_country

NEGATION_WINDOW = 30
NEGATION_TOKENS = ("not ", "non-", "non ", "never ", "excluded", "no ")

_SYNONYM_KEYS = (
    "Swaziland", "Cape Verde", "Ivory Coast", "DRC", "DR Congo",
    "Congo-Kinshasa", "Congo-Brazzaville", "The Gambia",
    "Tanzania, United Republic of",
)
_ALL_NAMES = tuple(sorted(
    set(AFRICAN_COUNTRIES) | set(_SYNONYM_KEYS),
    key=len, reverse=True,
))
_COUNTRY_ALT = "|".join(re.escape(n) for n in _ALL_NAMES)

_P1 = re.compile(rf"({_COUNTRY_ALT})\s*[:\-]\s*([\d,]+)\b", re.IGNORECASE)
_P2 = re.compile(rf"({_COUNTRY_ALT})\s*\(\s*[Nn]\s*=\s*([\d,]+)\s*\)", re.IGNORECASE)
_P3 = re.compile(
    rf"({_COUNTRY_ALT})\s+(?:enrolled|randomised|randomized)\s+([\d,]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EnrolmentRow:
    country: str
    n: int


def _is_negated(text: str, match_start: int) -> bool:
    window = text[max(0, match_start - NEGATION_WINDOW): match_start].lower()
    return any(tok in window for tok in NEGATION_TOKENS)


def extract_country_enrolment(text: str) -> list[EnrolmentRow]:
    if not text:
        return []
    found: dict[str, int] = {}
    for pat in (_P1, _P2, _P3):
        for m in pat.finditer(text):
            if _is_negated(text, m.start()):
                continue
            n_str = m.group(2).replace(",", "")
            try:
                n = int(n_str)
            except ValueError:
                continue
            canon = normalise_country(m.group(1))
            if canon is None:
                continue
            if n > found.get(canon, 0):
                found[canon] = n
    return [EnrolmentRow(country=c, n=n) for c, n in sorted(found.items())]
