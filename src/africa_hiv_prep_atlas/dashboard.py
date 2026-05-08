"""Self-contained dashboard.html generator (inline SVG, no CDN)."""
from __future__ import annotations

import html as _html
import json

LS_NAMESPACE = "ahpa-v0.1.0-"


def _row_to_tr(r: dict) -> str:
    cells = [
        _html.escape(str(r["ma_id"])),
        _html.escape(str(r["trial_id"])),
        "✓" if r["claimed_union"] else "—",
        "✓" if r["truth_d3"] else "—",
        "TP" if r["tp_at_d3"] else "FP" if r["fp_at_d3"] else "FN" if r["fn_at_d3"] else "TN",
    ]
    return "<tr><td>" + "</td><td>".join(cells) + "</td></tr>"


def _fmt_ci(val: float, lo: float, hi: float) -> str:
    """Format as 'X.XX (X.XX-X.XX)' with ASCII hyphen for ranges.

    Returns 'undefined' when val is NaN (e.g. D1 specificity when all trials are African).
    """
    import math
    if math.isnan(val):
        return "undefined"
    lo_str = f"{lo:.2f}" if not math.isnan(lo) else "nan"
    hi_str = f"{hi:.2f}" if not math.isnan(hi) else "nan"
    return f"{val:.2f} ({lo_str}-{hi_str})"


def _render_sweep_table(sweep: dict) -> str:
    """Render the D1/D2/D3 sensitivity sweep as an HTML table."""
    rows_html_parts = []
    defns = [
        ("d1", "D1: >=1 African site", False),
        ("d2", "D2: >=50% sites African", False),
        ("d3", "D3: >=50% enrolment African (primary)", True),
    ]
    for key, label, is_primary in defns:
        d = sweep.get(key, {})
        sens_str = _fmt_ci(d["sensitivity"], d["sens_ci"][0], d["sens_ci"][1])
        spec_str = _fmt_ci(d["specificity"], d["spec_ci"][0], d["spec_ci"][1])
        label_cell = f"<strong>{_html.escape(label)}</strong>" if is_primary else _html.escape(label)
        row_class = ' class="sweep-primary"' if is_primary else ""
        rows_html_parts.append(
            f"  <tr{row_class}><td>{label_cell}</td>"
            f"<td>{_html.escape(sens_str)}</td>"
            f"<td>{_html.escape(spec_str)}</td></tr>"
        )
    body = "\n".join(rows_html_parts)
    return (
        "<h2>Sensitivity sweep (pre-specified)</h2>\n"
        "<table>\n"
        "<thead><tr>"
        "<th>Definition</th>"
        "<th>Sensitivity (95% CI)</th>"
        "<th>Specificity (95% CI)</th>"
        "</tr></thead>\n"
        "<tbody>\n"
        f"{body}\n"
        "</tbody>\n"
        "</table>"
    )


def render_dashboard(rows: list[dict], headline: dict, sweep: dict | None = None) -> str:
    rows_html = "\n".join(_row_to_tr(r) for r in rows)
    headline_json = json.dumps(headline)
    sens_pct = f"{headline['sensitivity']:.2f}"
    spec_pct = f"{headline['specificity']:.2f}"
    sens_lo, sens_hi = headline["sens_ci"]
    spec_lo, spec_hi = headline["spec_ci"]
    sweep_section = _render_sweep_table(sweep) if sweep else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>African HIV PrEP/PEP Long-Acting Trial Atlas</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 1.5rem; max-width: 1100px; }}
h1 {{ font-size: 1.4rem; }}
.headline {{ background: #f5f5f5; padding: 1rem; border-left: 4px solid #2a6; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem; text-align: left; }}
.tp {{ background: #e7f5e7; }}
.fp {{ background: #fce7e7; }}
.fn {{ background: #fcf2e7; }}
.sweep-primary {{ font-weight: bold; background: #f0f4ff; }}
</style>
</head>
<body>
<h1>African HIV PrEP/PEP Long-Acting Trial Atlas v0.1.0</h1>
<div class="headline">
  <p><strong>Sensitivity:</strong> {sens_pct} (95% CI {sens_lo:.2f}-{sens_hi:.2f})</p>
  <p><strong>Specificity:</strong> {spec_pct} (95% CI {spec_lo:.2f}-{spec_hi:.2f})</p>
  <p><em>Method:</em> {_html.escape(headline.get("method", "?"))} - n_clusters={headline.get("n_clusters", "?")}</p>
</div>
{sweep_section}
<h2>Atlas rows</h2>
<table>
<thead><tr><th>MA</th><th>Trial</th><th>MA classified African?</th><th>Truth (D3)</th><th>Cell</th></tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
<script>
window.AHPA_HEADLINE = {headline_json};
try {{ localStorage.setItem("{LS_NAMESPACE}last-render", new Date().toISOString()); }} catch (e) {{}}
</script>
</body>
</html>"""
