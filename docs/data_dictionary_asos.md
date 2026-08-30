# Data Dictionary — ASOS Digital Experiments Dataset

Source: Liu, C.H.B., Cardoso, Â., Couturier, P., McCoy, E. (2021). *Datasets
for Online Controlled Experiments.* Published at https://osf.io/64jsb/.
78 real experiments run by a business unit within ASOS.com, 2019-2020.

## Raw schema

| Column | Type | Description |
|---|---|---|
| `experiment_id` | string | Anonymised experiment identifier |
| `variant_id` | int | ID of the **treatment** arm being compared to control at this row (control's own stats are in the `_c` columns of the same row — there are no separate control rows) |
| `metric_id` | int (1-4) | The organisational decision metric measured |
| `time_since_start` | float | Days since the experiment started, at this snapshot |
| `count_c`, `count_t` | float (integral) | Sample size in control / treatment at this snapshot |
| `mean_c`, `mean_t` | float | Sample mean of the metric in control / treatment |
| `variance_c`, `variance_t` | float | Sample variance in control / treatment (may be NaN — see below) |

## Profiling findings (from actually running the data, not assumed from the paper)

- **24,153 rows, 78 experiments, always exactly 4 metrics per experiment.**
- **Variant counts per experiment:** 57 experiments have 1 treatment arm
  (simple A/B), 13 have 2, and a handful have 3-4 — matches the paper's
  "2 to 5 variants per experiment" (variant IDs are 1-indexed against an
  implicit control, so "2 to 5 variants" = variant_id up to 4 observed here).
- **Metric type, determined empirically:** for `metric_id == 1`,
  `variance_c` equals `mean_c * (1 - mean_c)` to floating point precision
  in every row — i.e. it is a true Bernoulli/proportion metric (e.g. a
  conversion rate), and its variance is never missing. `metric_id` 2, 3,
  and 4 are real-valued/count metrics (means range from ~0 to ~150) whose
  variance is given directly and does NOT reduce to `p(1-p)`.
- **Missing variance:** 779/24,153 rows (3.2%) have `variance_c` or
  `variance_t` missing, **only** for metrics 2-4. We drop these rows rather
  than impute — a fabricated variance would silently corrupt every
  downstream p-value and CI.
- **Zero-sample rows:** 8 rows have `count_c == 0` or `count_t == 0` — a
  snapshot logged before that arm had accrued samples. Also dropped.
- **Snapshot frequency/duration:** experiments run a median of ~40 days of
  observed duration with a median of ~240 snapshots (some report
  more-than-daily, i.e. sub-daily, checkpoints).

## Known limitation (stated explicitly, not glossed over)

This is **group-level aggregated data**, not user-level. We can recompute
effect sizes, confidence intervals, and p-values correctly from the
provided sufficient statistics (n, mean, variance per arm), but we cannot:
- build a propensity/covariate model of who was assigned to which arm,
- run CUPED-style variance reduction using pre-experiment covariates,
- do individual-level heterogeneous treatment effect (HTE) analysis.

This is realistic: many real employers will also only be willing to share
aggregated experiment results rather than raw user-level logs, so working
correctly from summary statistics is itself the transferable skill being
demonstrated here.
