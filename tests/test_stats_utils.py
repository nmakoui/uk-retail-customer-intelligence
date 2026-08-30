"""
Validate our from-scratch test implementations against trusted reference
implementations (statsmodels), so a reviewer doesn't have to just take the
maths in stats_utils.py on faith.
"""
import numpy as np
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

from src.experimentation import stats_utils


def test_two_proportion_test_matches_statsmodels():
    n_c, n_t = 10000, 10000
    p_c, p_t = 0.10, 0.115
    count_c, count_t = p_c * n_c, p_t * n_t

    ours = stats_utils.two_proportion_test(n_c, n_t, p_c, p_t)

    z_ref, p_ref = proportions_ztest([count_t, count_c], [n_t, n_c])

    assert abs(ours.z - z_ref) < 1e-6
    assert abs(ours.p_value - p_ref) < 1e-6


def test_two_proportion_ci_reasonable_width():
    ours = stats_utils.two_proportion_test(100000, 100000, 0.20, 0.21)
    assert ours.ci_low < ours.abs_effect < ours.ci_high
    # sanity: CI width should be small with n=100k per arm
    assert (ours.ci_high - ours.ci_low) < 0.02


def test_welch_mean_test_zero_effect_gives_high_p_value():
    res = stats_utils.welch_mean_test(
        n_c=5000, n_t=5000, mean_c=10.0, mean_t=10.0, var_c=4.0, var_t=4.0
    )
    assert res.p_value > 0.9
    assert abs(res.abs_effect) < 1e-9


def test_welch_mean_test_large_effect_is_significant():
    res = stats_utils.welch_mean_test(
        n_c=5000, n_t=5000, mean_c=10.0, mean_t=10.5, var_c=4.0, var_t=4.0
    )
    assert res.p_value < 0.05
    assert res.abs_effect > 0


def test_run_test_dispatches_on_metric_type():
    import pandas as pd
    row_binary = pd.Series({
        "metric_type": "binary", "count_c": 1000, "count_t": 1000,
        "mean_c": 0.1, "mean_t": 0.12,
    })
    row_cont = pd.Series({
        "metric_type": "continuous", "count_c": 1000, "count_t": 1000,
        "mean_c": 5.0, "mean_t": 5.2, "variance_c": 2.0, "variance_t": 2.1,
    })
    r1 = stats_utils.run_test(row_binary)
    r2 = stats_utils.run_test(row_cont)
    assert r1.metric_type == "binary"
    assert r2.metric_type == "continuous"


def test_division_by_zero_guarded_in_pipeline():
    # count_c/count_t == 0 rows are filtered upstream by data_loader;
    # this test documents WHY, by showing the function itself does not
    # guard against it (so the upstream filter is load-bearing, not optional).
    try:
        stats_utils.two_proportion_test(0, 0, 0.0, 0.0)
        raised = False
    except ZeroDivisionError:
        raised = True
    assert raised, (
        "two_proportion_test no longer raises on n_c=n_t=0 - if this "
        "changed intentionally, also revisit data_loader.drop_zero_count_rows"
    )
