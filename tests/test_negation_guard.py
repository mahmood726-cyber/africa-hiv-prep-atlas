"""DossierGap 2026-04-15 lesson: 30-char preceding-window negation guard."""
from africa_hiv_prep_atlas.enrolment import extract_country_enrolment


def test_skips_not_randomised():
    text = "Final cohort. Not randomised: Kenya: 1,807. The trial was comprehensive. Kenya: 5,050."
    rows = extract_country_enrolment(text)
    kenyas = [r for r in rows if r.country == "Kenya"]
    assert len(kenyas) == 1
    assert kenyas[0].n == 5050


def test_skips_excluded():
    text = "Excluded Uganda: 200. Study sites included: Uganda: 1,500."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Uganda" and r.n == 1500 for r in rows)
    assert not any(r.country == "Uganda" and r.n == 200 for r in rows)


def test_skips_never():
    text = "South Africa: never enrolled (site closed). Botswana: 800 enrolled."
    rows = extract_country_enrolment(text)
    assert not any(r.country == "South Africa" for r in rows)


def test_negation_window_is_30_chars():
    text = "We will not address site issues at all. Kenya: 1000 randomised."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Kenya" and r.n == 1000 for r in rows)
