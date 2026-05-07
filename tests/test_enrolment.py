from africa_hiv_prep_atlas.enrolment import extract_country_enrolment, EnrolmentRow


def test_simple_pattern():
    text = "South Africa: 1,200 randomised. Uganda: 450 randomised."
    rows = extract_country_enrolment(text)
    assert EnrolmentRow(country="South Africa", n=1200) in rows
    assert EnrolmentRow(country="Uganda", n=450) in rows


def test_n_equals_format():
    text = "Botswana (n=890), Kenya (n=1100), Malawi (n=315)"
    rows = extract_country_enrolment(text)
    cs = {r.country for r in rows}
    assert {"Botswana", "Kenya", "Malawi"}.issubset(cs)


def test_skips_non_african():
    text = "USA: 500. South Africa: 1200."
    rows = extract_country_enrolment(text)
    assert all(r.country != "USA" for r in rows)
    assert any(r.country == "South Africa" for r in rows)


def test_canonicalises_synonyms():
    text = "Swaziland: 200 randomised."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Eswatini" for r in rows)


def test_thousands_separator():
    text = "Nigeria: 2,500 enrolled."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Nigeria" and r.n == 2500 for r in rows)


def test_empty_text():
    assert extract_country_enrolment("") == []
    assert extract_country_enrolment("no countries mentioned here") == []


def test_dedup_keeps_max():
    text = "Kenya: 100 randomised. Kenya enrolled 450."
    rows = extract_country_enrolment(text)
    kenyas = [r for r in rows if r.country == "Kenya"]
    assert len(kenyas) == 1
    assert kenyas[0].n == 450
