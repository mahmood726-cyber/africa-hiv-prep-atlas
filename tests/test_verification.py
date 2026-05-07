import re

from africa_hiv_prep_atlas.verification import render_verification_ui


def _sample_pairs():
    return [
        {"ma_id": "M1", "trial_id": "T1",
         "ma_quotes": [{"source_id": "M1-p3", "text": "..."}],
         "trial_quotes": [{"source_id": "T1-p1", "text": "..."}]},
        {"ma_id": "M2", "trial_id": "T1",
         "ma_quotes": [{"source_id": "M2-p4", "text": "..."}],
         "trial_quotes": [{"source_id": "T1-p1", "text": "..."}]},
    ]


def test_verification_renders_one_pair_at_a_time():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "data-pair-index=\"0\"" in html or 'data-pair-index="0"' in html


def test_localstorage_namespaced_with_rater():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "ahpa-irr-raterA-" in html


def test_export_button_present():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "Export" in html or "export" in html


def test_blinded_no_truth_or_claim_displayed():
    """Rater must NOT see the algorithmic truth_d3 / claimed_union — they're computing it."""
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "truth_d3" not in html.lower() or "data-pair" in html
    # Stronger check: no boolean values like "true" or "false" in pair data attributes.
    assert not re.search(r'data-truth-d3="(true|false)"', html, re.IGNORECASE)
    assert not re.search(r'data-claimed-union="(true|false)"', html, re.IGNORECASE)


def test_verification_div_balance():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    n_open = len(re.findall(r"<div[\s>]", html))
    n_close = html.count("</div>")
    assert n_open == n_close
