# Phase 8 - ASOS Experimentation Re-analysis (real data, computed on 2026-08-27)

Dataset: ASOS Digital Experiments Dataset (Liu et al., 2021), 78 real experiments,
381 test/metric/variant combinations at their final recorded snapshot.

## 8a. Headline results

- Raw significance (p < 0.05), no correction: **105
  / 381 (27.6%)**
- After Benjamini-Hochberg correction, **within each experiment's own 4 metrics**:
  84 / 381
  (22.0%) remain significant
- After Benjamini-Hochberg correction, **across all 381
  tests in the dataset at once** (the stricter view):
  68 / 381
  (17.8%) remain significant

This gives us a real number to compare against the commonly cited rule of thumb
that roughly a quarter of online experiments show a statistically significant
result - useful context to quote and interpret carefully in a portfolio write-up,
not to over-claim from.

## Effect-stability check (novelty/primacy effect proxy)

Restricted to tests whose **final result was statistically significant**
(instability on a near-null effect is just noise wobbling around zero, not a
finding - checked separately below): of **105** significant
test/metric/variant series with at least 5 snapshots, **21** show
the effect's sign flipping after the first 20% of the observed run, i.e. the
concluding "winning" or "losing" call was not yet stable for a meaningful
part of the test.

For context, across *all* 354 series regardless of significance,
190 show a sign flip - much higher, exactly because most of
those are near-null effects where sign is meaningless noise. That contrast
is itself worth stating explicitly in a write-up: it is the difference
between a real methodological check and a spurious one.

See `figures/heterogeneity_examples.png` for the most heavily-monitored
significant examples. This remains a simple, explainable heuristic, not a
formal change-point test.

### Phase 8b - designing a new (SIMULATED) retention experiment

Scenario: a retention email sent to customers flagged high-churn-risk. Primary metric: repeat purchase within 30 days.

- Assumed baseline repeat-purchase rate: 12.0%
- Minimum detectable absolute effect: 1.2% (baseline -> 13.2%)
- alpha = 0.05, power = 0.8
- **Required sample size: 11,999 customers per arm (23,998 total)**

Simulated run (synthetic data, NOT observed) assuming the true effect equals the planned MDE:
- control rate: 0.1161, treatment rate: 0.1328
- observed effect: +0.0167 (95% CI [+0.0083, +0.0250])
- p-value: 9.174e-05


## Files produced
- `reports/asos_reanalysis_summary.csv` - full per-test results (effect, CI, raw p,
  both BH-adjusted p variants)
- `reports/figures/pvalue_histogram.png`
- `reports/figures/heterogeneity_examples.png`
