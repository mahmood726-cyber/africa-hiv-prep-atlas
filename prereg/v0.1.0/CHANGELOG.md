# prereg/v0.1.0/ — release-candidate snapshot

Tagged via `v0.1.0-rc1` on 2026-05-09. This is **NOT** the final v0.1.0 release;
it is a release-candidate that exercises the `v*` tag-trigger workflow path
(`.github/workflows/ots-on-tag.yml`) on a real tag, validating the OTS-stamping
pipeline end-to-end before the actual v0.1.0.

## What is frozen here

- `spec.md` — verbatim copy of `docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md` with `sentinel:skip-file` marker prepended.
- `atlas.csv` — 54 (MA, trial) pairs from 20 unique MAs across 7 LA-PrEP trials.
- `dashboard.html` — pre-IRR dashboard with 35% sensitivity / 71% specificity headline + D1/D2/D3 sweep + per-MA SVG matrix + per-MA stats table.

## What is NOT in this snapshot

- **Cohen's kappa from the n=30 blinded IRR audit** (Task 20). The audit must complete with kappa >= 0.80 on both layers before the final v0.1.0 tag.
- **OTS stamps** for these 3 files — the GitHub Actions workflow stamps them when this tag pushes. Once Bitcoin block confirmation lands (~24h), the daily `ots-upgrade-cron.yml` workflow upgrades the proofs in place.

## Difference vs `v0.1.0` (final)

The final `v0.1.0` will be tagged after:
1. n=30 IRR audit complete with kappa >= 0.80
2. Methods Note headline numbers refreshed if IRR shifts the rate
3. CITATION.cff updated with final DOI

The atlas.csv and dashboard.html in `prereg/v0.1.0/` may be re-frozen at that point if any (MA, trial) pair was reclassified during the IRR review.

## Pre-IRR working numbers

- Sensitivity at D3: **35% (95% CI 15-60%)**
- Specificity at D3: **71% (95% CI 44-94%)**
- Confusion at D3: TP=13, FP=5, FN=24, TN=12
- D2 sweep produces identical confusion matrix (robustness)
- D1 non-discriminating (TN=0)
- 12 of 20 MAs (60%) have 100% miss rate

These are paper-quality framings but pending IRR for final release.
