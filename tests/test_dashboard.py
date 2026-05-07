import re

from africa_hiv_prep_atlas.dashboard import render_dashboard


def _sample():
    rows = [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": True, "claimed_c": False, "claimed_union": True,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "tp_at_d3": True, "fp_at_d3": False, "fn_at_d3": False, "tn_at_d3": False,
         "confidence_layer_m": "high", "confidence_layer_t": "high"},
    ]
    headline = {"sensitivity": 0.8, "specificity": 0.9,
                "sens_ci": (0.7, 0.9), "spec_ci": (0.85, 0.95),
                "method": "clustered_bootstrap", "n_clusters": 12}
    return rows, headline


def test_dashboard_returns_full_html_doc():
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    assert html.startswith("<!doctype html>") or html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_dashboard_self_contained_no_external_cdn():
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    forbidden = ["cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com", "googleapis.com"]
    for u in forbidden:
        assert u not in html


def test_dashboard_no_literal_close_script_in_template_literal():
    """lessons.md JS rule: no literal </script> in template literals."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    # Only allowable instance: the actual closing </script> tags.
    # Total </script> count should equal total <script> count.
    assert html.count("<script") == html.count("</script>")


def test_dashboard_localstorage_keys_namespaced():
    """top-5-defects: localStorage keys must be project-namespaced."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    if "localStorage" in html:
        assert re.search(r"localStorage\.(get|set|remove)Item\([\"']ahpa-", html), (
            "localStorage keys must start with 'ahpa-' namespace"
        )


def test_dashboard_renders_headline_number():
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    assert "0.80" in html or "80" in html  # sensitivity point estimate
    assert "0.7" in html  # CI lower bound


def test_dashboard_div_balance():
    """Count <div[\\s>] vs </div>."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    n_open = len(re.findall(r"<div[\s>]", html))
    n_close = html.count("</div>")
    assert n_open == n_close, f"open={n_open} close={n_close}"
