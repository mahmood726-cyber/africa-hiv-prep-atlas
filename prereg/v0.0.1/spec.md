sentinel:skip-file
# African HIV PrEP/PEP Long-Acting Trial Atlas — v0.1.0 Design

> **Status:** approved 2026-05-07. Pre-implementation spec. Edits after this point require a `prereg-v0.1.0-amend-N` tag and an OTS re-stamp.
> **Long-term-plan id:** `africa-hiv-prep-atlas`
> **Objective anchor:** `q3-2026-canon-3-atlases` (1 of 3)
> **Effort:** M
> **Path:** `C:\Projects\africa-hiv-prep-atlas\` → github.com/mahmood726-cyber/africa-hiv-prep-atlas
> **Target venue:** Synthēsis Methods Note (≤400w, .docx A4 1.5spc, 11-pt Calibri, Vancouver refs)

## 0. Problem statement

Meta-analyses (MAs) of long-acting HIV PrEP modalities — long-acting injectable PrEP (cabotegravir, lenacapavir), dapivirine vaginal ring, and forthcoming long-acting implants — make claims, explicit or implicit, about African-cohort coverage. Reviewers, guideline panels, and policymakers consume those claims as a proxy for generalisability to African populations. **No prior audit calibrates whether MAs' African-cohort classifications match the underlying primary-publication enrolment data.** This atlas closes that gap.

## 1. Headline calibration

**Calibration target.** Each MA-cited long-acting PrEP trial is classified by the MA (explicitly or implicitly) as African-cohort or not. The audit compares each (MA, trial) classification against a pre-specified ground truth derived from primary publications, CT.gov, PACTR, and ICTRP-Africa cross-checks.

**Headline shape.**
> *Across N (MA, trial) pairs, MAs classified African-cohort long-acting PrEP trials with X% sensitivity / Y% specificity vs the ground-truth definition (≥50% enrolment from African sites). Median per-MA absolute count error: K trials [IQR]. (Clustered bootstrap 95% CI, clustered by MA.)*

**Falsifier.** If sensitivity ≥95% **and** |median count error| ≤1, the calibration headline is null and the paper is reframed as a "MAs are well-calibrated on African coverage" finding.

## 2. Scope

**In scope (S2).** All long-acting HIV PrEP modalities:
- Long-acting injectable PrEP (cabotegravir-LA, lenacapavir, follow-on injectables)
- Dapivirine vaginal ring (silicone monthly ring, follow-on rings)
- Future long-acting implants if any cited MA includes them

**Out of scope.**
- Oral PrEP (TDF/FTC, TAF/FTC) MAs
- HIV PEP (post-exposure prophylaxis) MAs — different therapeutic paradigm
- Treatment trials (ART) — different population

## 3. Ground-truth definition of "African-cohort trial"

**Primary (D3): enrolment-based, ≥50%.** A trial is African-cohort iff ≥50% of enrolled participants were enrolled at sites in African countries (54-country UN list).

**Sensitivity sweeps (pre-specified):**
- **D1: site-based, loose.** ≥1 trial site in any African country.
- **D2: site-share-based.** ≥50% of trial sites in African countries.

The headline reports D3; D1 and D2 are reported in a single sensitivity table without inferential adjustment.

**Negation guard.** All enrolment-fraction extraction regexes inspect the 30-character window preceding any `(\d+)\s+(participants|subjects|enrolled|randomised)` match for negation tokens (`not`, `non`, `never`, `excluded`). Lesson source: DossierGap 2026-04-15 (negated-counts silent corruption).

## 4. Audit unit and metric (U3)

**Primary unit: per-(MA, trial) pair.** Each (MA, trial) pair is one audit observation. Each pair has:
- `claimed_african_a` — explicit count claim by MA includes this trial as African (boolean)
- `claimed_african_b` — implicit-from-included-studies-table tags this trial as African-sited (boolean)
- `claimed_african_c` — narrative mention of this trial in an Africa-context (boolean)
- `claimed_union` — `a OR b OR c` (boolean, primary)
- `truth_d1`, `truth_d2`, `truth_d3` — ground-truth booleans

**Primary metric.** Sensitivity and specificity of `claimed_union` against `truth_d3`, with clustered bootstrap (1000 reps, MA-cluster) 95% CI.

**Secondary unit: per-MA aggregate.** Each MA → one observation: `|sum(claimed_union) − sum(truth_d3)|` over its cited trials. Report median, IQR.

**Sensitivity sweeps.**
- Layer-stripped: re-run primary on `claimed_a`-only and `(claimed_a OR claimed_b)`.
- Definition-stripped: re-run primary against `truth_d1`, `truth_d2`.

## 5. Sample frame and search strategy

**MA universe.** MAs published 2020-01-01 onwards (post HPTN 083/084 readout) covering ≥1 long-acting modality (S2). Inclusion criteria:
1. Title or abstract names a long-acting PrEP modality (cabotegravir, lenacapavir, dapivirine ring, etc.)
2. Reports a pooled effect estimate from ≥2 trials
3. Full text accessible

**Search.** Cochrane CDSR + PubMed + Epistemonikos with pre-registered search string. PRISMA-compliant flow committed to repo.

**Estimated k.** 10–20 MAs, ~6–10 cited LA trials each, ~70–150 (MA, trial) pairs.

**Trial universe (initial enumeration, non-exhaustive — full list locked at prereg).** HPTN 083, HPTN 084, ASPIRE (MTN-020), The Ring Study (IPM 027), MTN-025/HOPE, PURPOSE-1, PURPOSE-2, follow-on. Each trial gets one row in `trials.csv` with ground-truth enrolment per D3 + D1 + D2.

## 6. Extraction protocol

**Two layers.**
- **Layer T (truth).** Per-trial: extract enrolment-by-country from primary publication + CT.gov + PACTR + ICTRP-Africa. Compute `truth_d1`, `truth_d2`, `truth_d3`. Output: `trials.csv`.
- **Layer M (MA claim).** Per (MA, trial) pair: extract `claimed_a`, `claimed_b`, `claimed_c` from MA full text. Output: `atlas.csv`.

**Algorithmic-first, human-audited.** Layer-T extraction is partly algorithmic (regex + LLM-assisted on primary publications). Layer-M extraction is partly algorithmic (table parsing + narrative phrase matching). Each algorithmic output carries a confidence tier — `high` (regex match against locked pattern), `medium` (LLM-assisted with structured prompt), `low` (ambiguous / multi-match / negation-flagged). All `medium` and `low` outputs are flagged for mandatory human review. Locked patterns, LLM prompt scaffolding, and the `low`-flag rule list are finalised in the writing-plans phase.

**Source-line attribution.** Every cell in `atlas.csv` and `trials.csv` carries a `source_id` pointer to a fixture excerpt (verbatim text + page/section locator) committed to `fixtures/`. No source = no value.

## 7. IRR — dual-rater audit (PACTR Hiddenness pattern)

- **Single-rater algorithmic extraction on full sample.**
- **Blinded dual-rater audit on random n=30 (MA, trial) subset.** Both rater A (Mahmood) and rater B (TBD: co-rater from Makerere cohort or independent) re-extract `claimed_union` and `truth_d3` from raw fixtures, blinded to algorithmic output and to each other.
- **Cohen's κ** reported per layer. Acceptance gate: κ ≥0.80 on both layers.
- **Audit timing.** n=30 audit happens **after** prereg + initial extraction is OTS-stamped, **before** unblinding the algorithmic results.

## 8. Statistical analysis plan

- **Primary analysis.** Clustered bootstrap (1000 reps, MA-cluster) on per-(MA, trial) sensitivity + specificity at D3.
- **Sensitivity analyses.** Repeat primary at D1 and D2; report in one descriptive sensitivity table.
- **Per-MA secondary.** Median |claimed − truth| count error with IQR.
- **Multiple-comparison policy.** No correction for the headline (single primary sensitivity/specificity pair). All sensitivity comparisons descriptive, not inferential.
- **k<10 guard.** If ≤10 MAs survive inclusion, switch primary CI from clustered bootstrap to permutation test on the raw classification matrix; document switch in a release-note commit and amend-tag the prereg.
- **Reproducibility floor.** `atlas.csv` byte-pinned via test fixture; xoshiro128** PRNG seed in headline notebook (per advanced-stats.md numerical-stability rules).

## 9. Repo and artifacts

**Path.** `C:\Projects\africa-hiv-prep-atlas\` → github.com/mahmood726-cyber/africa-hiv-prep-atlas

**Outputs.**
- `atlas.csv` — one row per (MA, trial) pair, ~18 cols
- `trials.csv` — one row per LA-PrEP trial, ground-truth enrolment by country
- `mas.csv` — one row per included MA, search-strategy provenance
- `fixtures/` — verbatim source excerpts referenced by `source_id` columns
- `dashboard.html` — filterable atlas, self-contained inline SVG (Trial Truthfulness pattern)
- `verification.html` — RapidMeta-style one-(MA, trial)-at-a-time UI with localStorage + JSON export, used to drive the n=30 blinded audit (ARAC Plan 3C pattern)
- `outputs/extraction_audit.md` — known limits, per-trial caveats (DossierGap pattern)
- `docs/synthesis-methods-note.docx` — ≤400w, A4 1.5spc, 11-pt Calibri, Vancouver refs
- `prereg/` — frozen spec snapshot per tag

**Tests.** pytest, target ≥80 tests at v0.1.0 (matches Trial Truthfulness 99 / Responder Floor 102). Mandatory:
- Negation-guard test (DossierGap lesson)
- Empty-DataFrame guard test (Sentinel P1-empty-dataframe-access)
- atlas.csv byte-pinning test
- Bootstrap seed-determinism test
- D1/D2/D3 ground-truth consistency test (D3 ⊆ D2 ⊆ D1 cardinality on the pinned trials.csv)

**Sentinel.** Pre-push hook installed; target 0 BLOCK at v0.1.0.

## 10. Pre-registration and Bitcoin anchoring

- **Spec freeze.** This document at v0.1.0-prereg before any (MA, trial) data extraction begins.
- **OTS-stamp 3 artifacts per release** (prereg, atlas.csv, dashboard.html). Internet Archive HTTP-200 check after Pages goes live.
- **Tag sequence.** `prereg-v0.0.1` → `prereg-v0.1.0-amend-N` (if needed) → `v0.1.0`.
- **Workbook entry.** Entry 680 (next after Tiba's 679). E156 micro-paper drafted parallel to v0.1.0; CURRENT BODY filled, YOUR REWRITE empty, SUBMITTED `[ ]`. MA listed as middle-author only per `feedback_e156_authorship.md`.

## 11. v0.1.0 acceptance criteria

| Gate | Threshold |
|---|---|
| MAs in `mas.csv` | ≥10 |
| LA trials in `trials.csv` | ≥6 |
| (MA, trial) pairs in `atlas.csv` | ≥50 |
| Cohen's κ on n=30 blinded audit | ≥0.80 (both layers) |
| Headline number with clustered-bootstrap CI | present in dashboard.html + Methods Note |
| Sentinel BLOCK | 0 |
| pytest pass rate | 100% |
| OTS stamps | 3/3 |
| GitHub Pages live + IA HTTP 200 | both pass |

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| k too small (≤10 MAs) → wide CI | k<10 guard switches CI method; document in commit |
| LA-PrEP MA universe still maturing (cabotegravir + lenacapavir programmes recent) | Time window post-2020 captures all readouts; recheck at v0.2.0 |
| MAs do not make explicit Africa claims (Layer (a) sparse) | Layer-stripped sensitivity sweep makes this an empirical finding, not a failure |
| Co-rater unavailable for n=30 audit | Defer v0.1.0 acceptance until rater B available; do not single-rate the IRR sample |
| Algorithmic extraction silently mis-classifies | Source-line attribution + fixture excerpts make every value re-verifiable |
| Domain replication of PACTR Hiddenness | Distinct comparator (primary-publication enrolment, not NCT-bridge); Methods Note explicitly contrasts |

## 13. Out-of-scope follow-ons (v0.2.0+)

- Oral PrEP MA expansion (S3 scope)
- Effect-heterogeneity audit (B3 framing — pooled vs African-subgroup HR)
- African-PI / African-coordinating-centre claim audit (D5 multi-criterion)
- MA-inclusion-completeness audit (B1 framing — direct PACTR-Hiddenness analogue)

These are explicitly deferred to keep v0.1.0 within Effort=M. Each is a separate atlas idea-candidate for the long-term plan.
