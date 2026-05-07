"""D1 / D2 / D3 ground-truth classification of trials."""
from __future__ import annotations

from africa_hiv_prep_atlas.countries import is_african
from africa_hiv_prep_atlas.records import Trial


def classify_d1(trial: Trial, sites_by_country: dict) -> bool:
    return any(is_african(c) and n > 0 for c, n in sites_by_country.items())


def classify_d2(trial: Trial, sites_by_country: dict) -> bool:
    total_sites = sum(sites_by_country.values())
    if total_sites <= 0:
        return False
    african_sites = sum(n for c, n in sites_by_country.items() if is_african(c))
    return (african_sites / total_sites) >= 0.5


def classify_d3(trial: Trial, sites_by_country: dict) -> bool:
    if trial.total_enrolled <= 0:
        return False
    return trial.african_fraction() >= 0.5


def classify_trial(trial: Trial, sites_by_country: dict) -> dict:
    return {
        "d1": classify_d1(trial, sites_by_country),
        "d2": classify_d2(trial, sites_by_country),
        "d3": classify_d3(trial, sites_by_country),
    }
