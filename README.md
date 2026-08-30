# UK Retail Customer Intelligence & Experimentation Platform

A portfolio project simulating a UK retail analytics consultancy running
three parallel client engagements. Full rationale and phase-by-phase plan:
see `docs/PROJECT_BLUEPRINT.md`.

**Status: Phase 8 (Experimentation) is built and running against real data.
Phases 1-7 (Online Retail II, Trustpilot NLP) are not started yet — see
`docs/impact_log.md` for progress.**

## What's actually implemented right now

`src/experimentation/` — a from-scratch re-analysis pipeline for the
**ASOS Digital Experiments Dataset** (Liu et al., 2021: 78 real A/B tests
run by ASOS.com, a UK fashion retailer), validated unit-test-by-unit-test
against `statsmodels` reference implementations. It:

1. Loads the raw aggregated snapshots and classifies each of the 4
   organisational metrics as binary (proportion) or continuous, based on
   actually profiling the data (metric 1's variance exactly matches
   `p(1-p)`; metrics 2-4 don't) — not assumed from the paper alone.
2. Handles two real data-quality issues found in the published file:
   ~3.2% of continuous-metric rows have a missing variance, and 8 rows
   have a zero sample count in one arm. Both are dropped and logged
   rather than silently imputed.
3. Re-computes the concluding effect, standard error, z-statistic,
   p-value and 95% CI for every (experiment, variant, metric) combination
   at its final snapshot — validated against `statsmodels.proportions_ztest`
   for the binary case.
4. Applies Benjamini-Hochberg FDR correction two ways (within each
   experiment's own 4 metrics, and across the whole 381-test collection)
   and reports how the "% significant" figure changes under each.
5. Checks effect **stability over time** for tests with ≥5 snapshots,
   restricted to tests that were actually significant at the end (checking
   near-null effects for "sign flips" would just be measuring noise).
6. Designs and powers a **new, hypothetical** retention-email experiment
   (Phase 8b), then simulates one run of it under the design assumptions —
   clearly labelled as synthetic, never presented as observed.

### Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.experimentation.run_reanalysis
pytest tests/ -v
```

Outputs land in `reports/` (`asos_reanalysis_summary.csv`,
`asos_reanalysis_report.md`) and `reports/figures/`.

### Headline results on the real data (see `reports/asos_reanalysis_report.md` for the live numbers)

- 27.6% of the 381 test/metric/variant combinations are significant at raw
  p < 0.05 — close to the ~25% figure often cited for this exact dataset,
  which is a nice sanity check that the re-implementation is correct.
- That drops to 22.0% (within-experiment FDR) and 17.8% (across-the-board
  FDR) after correcting for the fact most experiments test 4 metrics at
  once.
- Among the significant results, ~20% show the effect's sign flipping
  after the first fifth of the observation window — i.e. the final
  "winning" call wasn't stable throughout the test. Two of the plotted
  examples show a classic decaying novelty effect.

## What's next
- Phase 1-3: Online Retail II ETL + Postgres analytical layer
- Phase 5-7: Trustpilot NLP + churn/CLV models + SHAP explainability
- Phase 9-10: Power BI + AWS deployment

See `docs/PROJECT_BLUEPRINT.md` for the full plan and `docs/impact_log.md`
for what's been measured so far.
