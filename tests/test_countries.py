import pytest
from africa_hiv_prep_atlas.countries import (
    AFRICAN_COUNTRIES,
    is_african,
    normalise_country,
)


def test_count_is_54():
    assert len(AFRICAN_COUNTRIES) == 54


def test_includes_south_africa_uganda_botswana():
    for c in ("South Africa", "Uganda", "Botswana"):
        assert c in AFRICAN_COUNTRIES


def test_excludes_non_african_neighbours():
    for c in ("Israel", "Saudi Arabia", "Yemen", "Greece"):
        assert c not in AFRICAN_COUNTRIES


def test_is_african_case_insensitive():
    assert is_african("south africa")
    assert is_african("UGANDA")
    assert is_african("Botswana")


def test_handles_synonyms():
    assert is_african("Eswatini")
    assert is_african("Swaziland")
    assert is_african("Cabo Verde")
    assert is_african("Cape Verde")


def test_normalise_returns_canonical():
    assert normalise_country("swaziland") == "Eswatini"
    assert normalise_country("cape verde") == "Cabo Verde"
    assert normalise_country("united states") is None


def test_rejects_unknown():
    assert not is_african("Atlantis")
    assert not is_african("")
