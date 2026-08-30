# Impact Log

Honest, demonstrable metrics only — see the project blueprint's rule:
never invent revenue/conversion impact the data can't support.

## Phase 8 — ASOS experimentation re-analysis

**Task:** re-analyse 78 real historical A/B tests with proper statistical
rigour (multiple-testing correction, effect stability over time), and
design + power one new hypothetical experiment.

- Snapshots processed: 24,153 raw rows → 23,366 after dropping known
  data-quality issues (missing variance, zero-count rows) → 381
  test/metric/variant combinations analysed at their final snapshot.
- Data-quality issues found and handled: 779 rows (3.2%) with missing
  variance, 8 rows with zero sample count — both identified by profiling
  the actual file, not assumed.
- Result: 27.6% of tests significant at raw p<0.05 (raw), falling to 22.0%
  (within-experiment BH-FDR) and 17.8% (across-the-board BH-FDR) —
  i.e. **roughly a third of "significant" raw results would not survive
  correction for multiple testing**, a concrete, quantified illustration
  of why the correction matters.
- Of the tests that remained significant, ~20% (21/105) showed the
  effect's sign flipping after the first fifth of the test's duration —
  meaning the "final" call wasn't stable for a meaningful part of the run.
- All statistical functions unit-tested against `statsmodels` reference
  implementations (6/6 tests passing) rather than only spot-checked by eye.
- Runtime: full re-analysis (load, test, correct, plot, write report) on
  the full published dataset completes in well under 10 seconds on a
  personal laptop.

## Not yet done (tracked so scope stays honest)
- Online Retail II ETL, statistical analysis, churn/CLV modelling — not
  started.
- Trustpilot NLP module — not started.
- Power BI dashboards — not started.
- AWS deployment — not started.
