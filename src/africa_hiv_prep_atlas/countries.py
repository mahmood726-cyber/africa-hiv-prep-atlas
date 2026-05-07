"""54-country UN list of African states with synonym handling."""
from __future__ import annotations

AFRICAN_COUNTRIES: frozenset[str] = frozenset({
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros",
    "Democratic Republic of the Congo", "Republic of the Congo",
    "Cote d'Ivoire", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea",
    "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea",
    "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar",
    "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique",
    "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe",
    "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa",
    "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda",
    "Zambia", "Zimbabwe",
})

assert len(AFRICAN_COUNTRIES) == 54

_SYNONYMS: dict[str, str] = {
    "swaziland": "Eswatini",
    "cape verde": "Cabo Verde",
    "ivory coast": "Cote d'Ivoire",
    "drc": "Democratic Republic of the Congo",
    "dr congo": "Democratic Republic of the Congo",
    "congo-kinshasa": "Democratic Republic of the Congo",
    "congo-brazzaville": "Republic of the Congo",
    "the gambia": "Gambia",
    "tanzania, united republic of": "Tanzania",
}
_CANONICAL_LC: dict[str, str] = {c.lower(): c for c in AFRICAN_COUNTRIES}


def normalise_country(name: str) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    if key in _CANONICAL_LC:
        return _CANONICAL_LC[key]
    if key in _SYNONYMS:
        return _SYNONYMS[key]
    return None


def is_african(name: str) -> bool:
    return normalise_country(name) is not None
