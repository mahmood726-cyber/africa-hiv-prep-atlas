# Extraction audit — africa-hiv-prep-atlas v0.1.0

> Per DossierGap pattern: known limits, per-trial caveats, residual uncertainty.
> Updated: 2026-05-07 (pre-IRR; will be refreshed after Task 20 audit results).

## Headline (pre-IRR)

**Across 54 (MA, trial) pairs in 20 long-acting HIV PrEP MAs (2020–2026), MAs
classified African-cohort trials with 35% sensitivity (95% CI 15–60%) and 71%
specificity (95% CI 44–94%) at the D3 ground truth (≥50% enrolment from African
sites). Method: clustered bootstrap, n_clusters=20.**

Confusion matrix: TP=13, FP=5, FN=24, TN=12.

Calibration finding: MAs systematically under-detect African-cohort coverage.
65% of actually-African long-acting PrEP trials (24/37) are cited but NOT
classified as African in any of three Layer-M layers (explicit count, table,
narrative).

## Trial-level caveats

| Trial | Caveat | Source |
|---|---|---|
| HPTN_083 | Mixed-region trial; only 1 of 7 sites in Africa (South Africa). Enrolment-by-country uses equal-distribution approximation across 7 countries → ~14% African enrolment. confidence_layer_t = "medium" pending v0.2.0 primary-publication extraction. | Landovitz 2021 NEJM PMID 34379922 |
| HPTN_084 | All 7 sites in Africa; total enrolment 3,224 distributed equally (460-462 per country) | Delany-Moretlwe 2022 Lancet PMID 35378077 |
| ASPIRE (MTN-020) | 5 sites listed in AACT; Zambia marked removed=t (excluded from active enrolment); 4 active African sites. Equal-distribution across 4 active countries (657-658 each, total 2629). | Baeten 2016 NEJM PMID 26900902 |
| RING_STUDY (IPM 027) | 3 sites listed in AACT; Rwanda marked removed=t; 2 active African sites. Equal-distribution across 2 (979-980 each, total 1959). | Nel 2016 NEJM PMID 27959766 |
| MTN_025_HOPE | 4 active African sites; equal distribution (364 each, total 1456). | Baeten 2021 Lancet HIV PMID 33539762 |
| PURPOSE_1 | 2 active African sites (South Africa, Uganda); AACT enrolment 5368 vs paper-reported ITT 5338 (30 screened-out). Equal-distribution (2684 each). | Bekker 2024 NEJM PMID 39046157 |
| PURPOSE_2 | Mixed-region trial; 1 of 8 sites in Africa (South Africa). Equal-distribution → ~12.5% African. confidence_layer_t = "medium". | Kelley 2024 NEJM PMID 39602624 |

## MA-level caveats

- 7 MAs use abstract-only Layer-M extraction (no PMC full text available):
  chen-2023-rev-med-virol (Chen 2023), chou-2023-jama (Chou 2023),
  garratt-2025-aids (Garratt 2025), makoni-2024-aids-behav (Makoni 2024),
  mukuhlani-2026-int-j-infect-dis (Mukuhlani 2026),
  musekiwa-2020-trop-med-int-health (Musekiwa 2020),
  obiero-2021-cochrane-db-syst-rev (Obiero 2021).
  For these, confidence_layer_m = "medium".

- Cost-effectiveness MAs (xi-2025-j-int-aids-soc [Xi 2025],
  bozzani-2022-pharmacoeconomics [Bozzani 2022]) cite trials by numbered
  references rather than by trial-name in body text → all Layer-M (a/b/c)
  booleans = FALSE despite the trials being legitimately cited and
  African-cohort. These contribute 5 of the 24 False Negatives.
  **This is itself a calibration finding**: economic MAs do NOT make narrative
  African-cohort claims even when their cohorts are African.

- 18-of-20 MAs are systematic reviews / meta-analyses by article_type. 2 are
  listed in PubMed as both Systematic Review and Journal Article without
  explicit "Meta-Analysis" tag: sharma-2024-clin-infect-dis (Sharma 2024
  ciad537) and sharma-bhavesh-2026-cureus (Sharma B 2026 cureus); included
  under inclusion criterion #2 (pooled effect estimate from ≥2 trials).

## Negation-guard hits

Currently zero, since enrolment data is sourced from AACT structured fields,
not free-text. v0.2.0 will sweep primary-publication enrolment tables and
surface negation-guard exclusions per the DossierGap pattern.

## Residual uncertainty (pre-IRR)

- **Layer-M LLM judgment**: Phase 1 extraction was LLM-assisted (Claude
  Sonnet 4.6) on 54 (MA, trial) pairs. Cohen's κ vs blinded human auditor
  will be reported in v0.1.0 final per Task 20 protocol.
- **Equal-distribution enrolment** for multi-country trials approximates
  per-country enrolment at total/N. Distribution within African sites does
  not affect D3 (≥50% African) classification but does affect downstream
  subgroup analyses.
- **CIs are wide**: sensitivity 95% CI 15–60% spans 45 percentage points.
  Effective k (independent MAs) is small; the n=30 audit will tighten this.
- **Cochrane MAs** (obiero-2021-cochrane-db-syst-rev [Obiero 2021],
  ebrahim-2026-cochrane-db-syst-rev [Ebrahim 2026]) cite only 2 trials each
  in the current extraction; full-text re-pass may find additional cited
  trials. v0.2.0 sweep target.
- **Search restricted to PubMed**; Cochrane CDSR + Epistemonikos searches
  deferred to v0.2.0 per `docs/prisma_flow.md`.

## Trust-but-verify checklist (for the IRR rater)

When the n=30 IRR audit is run via `outputs/verification.html`:
1. Confirm trial-extraction matches AACT (sites match countries.txt, total
   matches studies.txt enrolment column).
2. Confirm MA cite-trail by matching the verbatim_quotes against the MA
   full text.
3. Document any discrepancies in `outputs/irr_audit_results.json` along
   with κ values.
