"""RapidMeta-style one-(MA, trial)-at-a-time IRR audit UI (ARAC Plan 3C)."""
from __future__ import annotations

import html as _html
import json

LS_NAMESPACE = "ahpa-irr-"


def _quote_block(quotes: list[dict]) -> str:
    items = []
    for q in quotes:
        items.append(
            f'<blockquote data-src="{_html.escape(q["source_id"])}">'
            f'<small>{_html.escape(q["source_id"])}</small><br>'
            f'{_html.escape(q["text"])}</blockquote>'
        )
    return "\n".join(items)


def render_verification_ui(pairs: list[dict], rater_id: str) -> str:
    pair_blocks = []
    for i, p in enumerate(pairs):
        pair_blocks.append(f"""
<section class="pair" data-pair-index="{i}" data-pair-id="{_html.escape(p['ma_id'])}__{_html.escape(p['trial_id'])}" hidden>
  <h2>Pair {i + 1} of {len(pairs)}: {_html.escape(p['ma_id'])} × {_html.escape(p['trial_id'])}</h2>
  <h3>MA evidence</h3>
  {_quote_block(p['ma_quotes'])}
  <h3>Trial evidence</h3>
  {_quote_block(p['trial_quotes'])}
  <fieldset>
    <legend>Did the MA classify this trial as African-cohort? (any of a/b/c)</legend>
    <label><input type="radio" name="claim-{i}" value="true"> Yes</label>
    <label><input type="radio" name="claim-{i}" value="false"> No</label>
  </fieldset>
  <fieldset>
    <legend>Is the trial African-cohort under D3 (≥50% enrolment)?</legend>
    <label><input type="radio" name="truth-{i}" value="true"> Yes</label>
    <label><input type="radio" name="truth-{i}" value="false"> No</label>
  </fieldset>
  <button type="button" data-action="next">Save and next</button>
</section>""")
    rater_safe = _html.escape(rater_id)
    ns_val = LS_NAMESPACE + rater_safe + "-"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRR Audit — Rater {rater_safe}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 1.5rem; max-width: 800px; }}
.pair {{ border: 1px solid #ccc; padding: 1rem; margin: 1rem 0; }}
blockquote {{ border-left: 3px solid #aac; padding-left: 0.6rem; margin: 0.5rem 0; }}
fieldset {{ margin: 0.6rem 0; }}
</style>
</head>
<body>
<h1>IRR Audit — Rater <code>{rater_safe}</code></h1>
<p>Read each MA quote and trial quote, then answer both questions. <strong>You are blinded to the algorithmic answers.</strong></p>
<div id="pairs">
{"".join(pair_blocks)}
</div>
<button id="export" type="button">Export JSON</button>
<pre id="export-out"></pre>
<script>
const RATER = "{rater_safe}";
const NS = "{ns_val}";
const pairs = document.querySelectorAll("section.pair");
let idx = 0;
function show(i) {{
  pairs.forEach(p => p.hidden = true);
  if (i < pairs.length) {{
    pairs[i].hidden = false;
  }}
}}
show(0);
document.querySelectorAll('button[data-action="next"]').forEach(btn => {{
  btn.addEventListener("click", () => {{
    const sec = btn.closest("section.pair");
    const id = sec.dataset.pairId;
    const claim = sec.querySelector(`input[name="claim-${{sec.dataset.pairIndex}}"]:checked`);
    const truth = sec.querySelector(`input[name="truth-${{sec.dataset.pairIndex}}"]:checked`);
    if (!claim || !truth) {{ alert("Please answer both."); return; }}
    try {{
      localStorage.setItem(NS + id, JSON.stringify({{
        claim: claim.value === "true", truth: truth.value === "true",
        ts: new Date().toISOString()
      }}));
    }} catch (e) {{}}
    idx += 1;
    show(idx);
  }});
}});
document.getElementById("export").addEventListener("click", () => {{
  const out = {{}};
  for (let k = 0; k < localStorage.length; k++) {{
    const key = localStorage.key(k);
    if (key && key.startsWith(NS)) {{
      out[key.slice(NS.length)] = JSON.parse(localStorage.getItem(key));
    }}
  }}
  document.getElementById("export-out").textContent = JSON.stringify(out, null, 2);
}});
</script>
</body>
</html>"""
