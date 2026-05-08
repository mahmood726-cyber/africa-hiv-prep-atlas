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


CELL_COLORS = {
    "tp": "#9be09b",  # correct positive (MA correctly classified African-cohort)
    "fp": "#f29b9b",  # wrongly claimed African
    "fn": "#f4a261",  # missed African (the calibration gap)
    "tn": "#d3d3d3",  # correct negative
    "nc": "#ffffff",  # trial not cited by this MA
}


def _classify_cell(r: dict | None) -> str:
    if r is None:
        return "nc"
    if r.get("tp_at_d3"):
        return "tp"
    if r.get("fp_at_d3"):
        return "fp"
    if r.get("fn_at_d3"):
        return "fn"
    return "tn"


def _render_per_ma_matrix(rows: list[dict]) -> str:
    """Inline-SVG matrix: rows=MAs, cols=trials, cells colored by confusion class.

    Visualises which MAs drive each FP/FN cell - the kind of figure that goes
    in a paper. White cells = trial not cited by that MA.
    """
    if not rows:
        return ""
    ma_ids = sorted({r["ma_id"] for r in rows})
    trial_ids = sorted({r["trial_id"] for r in rows})
    by_pair = {(r["ma_id"], r["trial_id"]): r for r in rows}

    cell = 22
    label_left = 240
    label_top = 110
    width = label_left + cell * len(trial_ids) + 20
    height = label_top + cell * len(ma_ids) + 80

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Per-MA confusion matrix" '
        f'style="font-family: -apple-system, system-ui, sans-serif; font-size: 11px;">'
    ]
    # Column labels (rotated)
    for j, tid in enumerate(trial_ids):
        x = label_left + j * cell + cell / 2
        parts.append(
            f'<text x="{x}" y="{label_top - 8}" text-anchor="end" '
            f'transform="rotate(-50 {x},{label_top - 8})">{_html.escape(tid)}</text>'
        )
    # Row labels + cells
    for i, ma in enumerate(ma_ids):
        y_label = label_top + i * cell + cell - 6
        ma_short = ma if len(ma) <= 36 else ma[:33] + "..."
        parts.append(
            f'<text x="{label_left - 6}" y="{y_label}" text-anchor="end">{_html.escape(ma_short)}</text>'
        )
        for j, tid in enumerate(trial_ids):
            r = by_pair.get((ma, tid))
            cls = _classify_cell(r)
            color = CELL_COLORS[cls]
            x = label_left + j * cell
            y = label_top + i * cell
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell - 1}" height="{cell - 1}" '
                f'fill="{color}" stroke="#999" stroke-width="0.5">'
                f'<title>{_html.escape(ma)} x {_html.escape(tid)}: {cls.upper()}</title>'
                f'</rect>'
            )
    # Legend
    legend_y = label_top + cell * len(ma_ids) + 24
    legend_items = [
        ("tp", "True positive (MA correctly classified African)"),
        ("fp", "False positive (MA wrongly claimed African)"),
        ("fn", "False negative (MA missed African-cohort trial)"),
        ("tn", "True negative (correctly non-African)"),
        ("nc", "Trial not cited by this MA"),
    ]
    lx = label_left
    for cls, label in legend_items:
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="14" height="14" '
            f'fill="{CELL_COLORS[cls]}" stroke="#999" stroke-width="0.5"/>'
            f'<text x="{lx + 18}" y="{legend_y + 11}">{_html.escape(label)}</text>'
        )
        lx += 240
        if lx > width - 100:
            lx = label_left
            legend_y += 18
    parts.append("</svg>")
    return (
        "<h2>Per-MA confusion matrix</h2>\n"
        '<p style="font-size: 0.9rem; color: #666;">Each cell is one (MA, trial) pair. '
        'Orange = false negative (MA cited an African-cohort trial without classifying it as African) - '
        'these cells are the calibration gap.</p>\n'
        + "".join(parts)
    )


def render_dashboard(rows: list[dict], headline: dict, sweep: dict | None = None) -> str:
    rows_html = "\n".join(_row_to_tr(r) for r in rows)
    headline_json = json.dumps(headline)
    sens_pct = f"{headline['sensitivity']:.2f}"
    spec_pct = f"{headline['specificity']:.2f}"
    sens_lo, sens_hi = headline["sens_ci"]
    spec_lo, spec_hi = headline["spec_ci"]
    sweep_section = _render_sweep_table(sweep) if sweep else ""
    matrix_section = _render_per_ma_matrix(rows)
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
{matrix_section}
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
