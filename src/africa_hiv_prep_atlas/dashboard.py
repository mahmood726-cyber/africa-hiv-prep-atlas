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


def render_dashboard(rows: list[dict], headline: dict) -> str:
    rows_html = "\n".join(_row_to_tr(r) for r in rows)
    headline_json = json.dumps(headline)
    sens_pct = f"{headline['sensitivity']:.2f}"
    spec_pct = f"{headline['specificity']:.2f}"
    sens_lo, sens_hi = headline["sens_ci"]
    spec_lo, spec_hi = headline["spec_ci"]
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
</style>
</head>
<body>
<h1>African HIV PrEP/PEP Long-Acting Trial Atlas v0.1.0</h1>
<div class="headline">
  <p><strong>Sensitivity:</strong> {sens_pct} (95% CI {sens_lo:.2f}–{sens_hi:.2f})</p>
  <p><strong>Specificity:</strong> {spec_pct} (95% CI {spec_lo:.2f}–{spec_hi:.2f})</p>
  <p><em>Method:</em> {_html.escape(headline.get("method", "?"))} · n_clusters={headline.get("n_clusters", "?")}</p>
</div>
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
