"""
stats_utils.py
---------------
Re-implements the hypothesis test each ASOS experiment snapshot needs, from
the aggregated summary statistics only (count, mean, variance per arm) -
because that is genuinely all the dataset gives us, and it is genuinely all
most companies will hand a new hire on day one either.

Two test types, matched to the metric type discovered in data_loader.py:

1. Two-proportion z-test (metric_type == "binary")
   Standard pooled-variance test for a difference in conversion rates.

2. Welch's t-test approximation for two independent means
   (metric_type == "continuous")
   We use the samples' own reported variances (unequal-variance / Welch
   assumption, which is the safer default), and because sample sizes here
   are typically in the hundreds of thousands to tens of millions, the
   t-distribution collapses to the standard normal - we use the normal
   approximation directly and note this explicitly rather than silently
   assuming it.

Both return a common result shape: effect (absolute and relative), standard
error, z-statistic, two-sided p-value, and a 95% confidence interval on the
absolute effect.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class TestResult:
    n_c: float
    n_t: float
    mean_c: float
    mean_t: float
    abs_effect: float          # mean_t - mean_c
    rel_effect: float          # (mean_t - mean_c) / mean_c, may be inf/nan if mean_c == 0
    se: float
    z: float
    p_value: float
    ci_low: float
    ci_high: float
    metric_type: str


def two_proportion_test(n_c, n_t, p_c, p_t, alpha: float = 0.05) -> TestResult:
    """Pooled two-proportion z-test. p_c/p_t are rates in [0, 1]."""
    n_c, n_t, p_c, p_t = float(n_c), float(n_t), float(p_c), float(p_t)

    pooled_p = (p_c * n_c + p_t * n_t) / (n_c + n_t)
    se_pooled = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n_c + 1 / n_t))

    abs_effect = p_t - p_c
    z = abs_effect / se_pooled if se_pooled > 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    # CI on the absolute effect uses the *unpooled* SE (standard practice
    # for interval estimation, even though the test itself is pooled).
    se_unpooled = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_low = abs_effect - z_crit * se_unpooled
    ci_high = abs_effect + z_crit * se_unpooled

    rel_effect = abs_effect / p_c if p_c != 0 else np.nan

    return TestResult(
        n_c=n_c, n_t=n_t, mean_c=p_c, mean_t=p_t,
        abs_effect=abs_effect, rel_effect=rel_effect,
        se=se_unpooled, z=z, p_value=p_value,
        ci_low=ci_low, ci_high=ci_high, metric_type="binary",
    )


def welch_mean_test(n_c, n_t, mean_c, mean_t, var_c, var_t,
                     alpha: float = 0.05) -> TestResult:
    """Welch (unequal-variance) two-sample test using normal approximation,
    valid given the very large sample sizes in this dataset."""
    n_c, n_t = float(n_c), float(n_t)
    mean_c, mean_t = float(mean_c), float(mean_t)
    var_c, var_t = float(var_c), float(var_t)

    se = np.sqrt(var_c / n_c + var_t / n_t)
    abs_effect = mean_t - mean_c
    z = abs_effect / se if se > 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_low = abs_effect - z_crit * se
    ci_high = abs_effect + z_crit * se

    rel_effect = abs_effect / mean_c if mean_c != 0 else np.nan

    return TestResult(
        n_c=n_c, n_t=n_t, mean_c=mean_c, mean_t=mean_t,
        abs_effect=abs_effect, rel_effect=rel_effect,
        se=se, z=z, p_value=p_value,
        ci_low=ci_low, ci_high=ci_high, metric_type="continuous",
    )


def run_test(row) -> TestResult:
    """Dispatch a single dataframe row (with a `metric_type` column already
    attached by data_loader.add_metric_type) to the right test."""
    if row["metric_type"] == "binary":
        return two_proportion_test(row["count_c"], row["count_t"],
                                    row["mean_c"], row["mean_t"])
    return welch_mean_test(row["count_c"], row["count_t"],
                            row["mean_c"], row["mean_t"],
                            row["variance_c"], row["variance_t"])
