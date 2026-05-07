"""
Test suite for trial fixtures.

Validates schema and attribution of trial JSONs under fixtures/trials/.
Tests skip gracefully when fixtures are not yet populated (Task 13 USER ACTION pending).
"""

import json
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "trials"


def _fixture_files():
    """Return sorted list of trial fixture JSON files."""
    return sorted(FIXTURE_DIR.glob("*.json"))


def test_at_least_6_trials():
    """Require at least 6 trial fixtures (HPTN_083, HPTN_084, ASPIRE, RING_STUDY, MTN_025_HOPE, +1)."""
    files = _fixture_files()
    if not files:
        pytest.skip(
            "USER ACTION pending: populate fixtures/trials/ with ≥6 LA-PrEP trial JSONs "
            "(HPTN_083, HPTN_084, ASPIRE, RING_STUDY, MTN_025_HOPE, IPM_027). "
            "See docs/fixture_seeding_protocol.md"
        )
    assert len(files) >= 6, f"Expected ≥6 trial fixtures, got {len(files)}"


def test_each_fixture_has_required_keys():
    """Each trial fixture must have all required keys."""
    required_keys = {
        "trial_id", "nct", "pactr", "modality", "year",
        "enrolment_by_country", "sites_by_country", "total_enrolled",
        "source_id", "verbatim_excerpts"
    }
    for fixture_file in _fixture_files():
        with open(fixture_file) as f:
            trial = json.load(f)
        missing = required_keys - set(trial.keys())
        assert not missing, (
            f"{fixture_file.name}: missing keys {missing}"
        )
        # Verify types
        assert isinstance(trial["trial_id"], str)
        assert isinstance(trial["nct"], (str, type(None)))
        assert isinstance(trial["pactr"], (str, type(None)))
        assert isinstance(trial["modality"], str)
        assert isinstance(trial["year"], int)
        assert isinstance(trial["enrolment_by_country"], dict)
        assert isinstance(trial["sites_by_country"], dict)
        assert isinstance(trial["total_enrolled"], int)
        assert isinstance(trial["source_id"], str)
        assert isinstance(trial["verbatim_excerpts"], list)


def test_each_fixture_has_at_least_one_verbatim_excerpt():
    """Each trial fixture must have at least one verbatim excerpt with required fields."""
    required_excerpt_keys = {"source_id", "locator", "text"}
    for fixture_file in _fixture_files():
        with open(fixture_file) as f:
            trial = json.load(f)
        assert len(trial["verbatim_excerpts"]) > 0, (
            f"{fixture_file.name}: no verbatim_excerpts"
        )
        for i, excerpt in enumerate(trial["verbatim_excerpts"]):
            missing = required_excerpt_keys - set(excerpt.keys())
            assert not missing, (
                f"{fixture_file.name} excerpt {i}: missing {missing}"
            )
            assert isinstance(excerpt["text"], str) and excerpt["text"].strip(), (
                f"{fixture_file.name} excerpt {i}: text is empty or not a string"
            )


def test_each_fixture_total_matches_country_sum():
    """Total enrolled >= sum of country enrollments (slack permitted)."""
    for fixture_file in _fixture_files():
        with open(fixture_file) as f:
            trial = json.load(f)
        country_sum = sum(trial["enrolment_by_country"].values())
        assert trial["total_enrolled"] >= country_sum, (
            f"{fixture_file.name}: total_enrolled {trial['total_enrolled']} < "
            f"country sum {country_sum}"
        )


def test_each_fixture_classifies_under_at_least_d1():
    """Every fixture must have at least one site in an African country (D1 inclusion criterion)."""
    from africa_hiv_prep_atlas.countries import is_african

    for fixture_file in _fixture_files():
        with open(fixture_file) as f:
            trial = json.load(f)
        sites_by_country = trial.get("sites_by_country", {})
        african_sites = sum(
            count for country, count in sites_by_country.items()
            if is_african(country)
        )
        assert african_sites >= 1, (
            f"{fixture_file.name}: no sites found in African countries. "
            f"Countries present: {set(sites_by_country.keys())}. "
            f"Required ≥1 for D1 inclusion."
        )
