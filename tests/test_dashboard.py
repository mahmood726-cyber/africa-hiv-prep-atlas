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


def test_dashboard_renders_sensitivity_sweep():
    """Sweep table with D1/D2/D3 rows must appear in generated HTML."""
    rows, headline = _sample()
    sweep = {
        "d1": {"sensitivity": 0.90, "specificity": 0.60,
               "sens_ci": (0.80, 0.97), "spec_ci": (0.45, 0.73),
               "method": "clustered_bootstrap", "n_clusters": 12},
        "d2": {"sensitivity": 0.75, "specificity": 0.72,
               "sens_ci": (0.62, 0.86), "spec_ci": (0.58, 0.84),
               "method": "clustered_bootstrap", "n_clusters": 12},
        "d3": {"sensitivity": 0.35, "specificity": 0.71,
               "sens_ci": (0.15, 0.60), "spec_ci": (0.44, 0.94),
               "method": "clustered_bootstrap", "n_clusters": 12},
    }
    html = render_dashboard(rows, headline, sweep=sweep)
    assert "Sensitivity sweep" in html
    assert "D1" in html or ">=1 African site" in html
    assert "D2" in html or ">=50% sites" in html
    assert "D3" in html or ">=50% enrolment" in html
    # Point estimates for each definition
    assert "0.90" in html  # D1 sensitivity
    assert "0.75" in html  # D2 sensitivity
    assert "0.35" in html  # D3 sensitivity


def test_dashboard_sweep_defaults_none_backward_compat():
    """Old callers that omit sweep argument should still get valid HTML."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    assert "</html>" in html
    assert "Sensitivity sweep" not in html


def test_dashboard_renders_per_ma_matrix_svg():
    rows = [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": False, "claimed_b": False, "claimed_c": False, "claimed_union": False,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "tp_at_d3": False, "fp_at_d3": False, "fn_at_d3": True, "tn_at_d3": False,
         "confidence_layer_m": "high", "confidence_layer_t": "high"},
        {"ma_id": "M2", "trial_id": "T2",
         "claimed_a": True, "claimed_b": True, "claimed_c": True, "claimed_union": True,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "tp_at_d3": True, "fp_at_d3": False, "fn_at_d3": False, "tn_at_d3": False,
         "confidence_layer_m": "high", "confidence_layer_t": "high"},
    ]
    headline = {"sensitivity": 0.5, "specificity": 1.0,
                "sens_ci": (0.0, 1.0), "spec_ci": (0.0, 1.0),
                "method": "clustered_bootstrap", "n_clusters": 2}
    html = render_dashboard(rows, headline)
    assert "<svg" in html
    assert "Per-MA confusion matrix" in html
    # Both MAs should appear as row labels and both trials as col labels
    assert ">M1<" in html and ">M2<" in html
    assert ">T1<" in html and ">T2<" in html
    # FN cell color (orange) must appear since M1 has fn_at_d3
    assert "#f4a261" in html
    # TP cell color (green) must appear since M2 has tp_at_d3
    assert "#9be09b" in html
