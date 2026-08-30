"""
power_analysis.py
------------------
Phase 8b of the project blueprint: design a NEW experiment, properly
powered, rather than only re-analysing historical ones.

Scenario used here (replace with your actual churn-model output once the
Online Retail II module exists): a retention email is sent to customers
flagged as high-churn-risk. The primary metric is whether the customer
places another order within 30 days of the email (a binary/proportion
metric - matching metric_id==1's type in the ASOS dataset, which is a
deliberate design choice so this module is a natural extension of the
re-analysis code above, not a separate one-off script).

IMPORTANT: Everything produced by `simulate_experiment()` in this file is
SYNTHETIC DATA generated under stated assumptions. It must never be
presented as an observed result - only as a demonstration of experiment
design and analysis method. Say so explicitly in any write-up.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from . import stats_utils


@dataclass
class PowerPlan:
    baseline_rate: float
    mde_absolute: float
    alpha: float
    power: float
    required_n_per_arm: int
    total_required_n: int


def required_sample_size(baseline_rate: float, mde_absolute: float,
                          alpha: float = 0.05, power: float = 0.8) -> PowerPlan:
    """Required sample size PER ARM for a two-proportion test, using
    Cohen's h effect size (the standard, variance-stabilising effect size
    for proportions), via statsmodels' NormalIndPower solver.
    """
    p1 = baseline_rate
    p2 = baseline_rate + mde_absolute
    effect_size = proportion_effectsize(p2, p1)  # Cohen's h

    analysis = NormalIndPower()
    n_per_arm = analysis.solve_power(
        effect_size=abs(effect_size), alpha=alpha, power=power,
        ratio=1.0, alternative="two-sided",
    )
    n_per_arm = int(np.ceil(n_per_arm))

    return PowerPlan(
        baseline_rate=baseline_rate, mde_absolute=mde_absolute,
        alpha=alpha, power=power,
        required_n_per_arm=n_per_arm, total_required_n=2 * n_per_arm,
    )


def simulate_experiment(plan: PowerPlan, seed: int = 42) -> dict:
    """Simulate ONE run of the planned experiment under the assumption that
    the true effect equals the MDE used to power it (i.e. the "we just hit
    our design target" scenario) - a common, honest way to sanity-check a
    power calculation before spending real budget on it.
    """
    rng = np.random.default_rng(seed)
    n = plan.required_n_per_arm
    p_c = plan.baseline_rate
    p_t = plan.baseline_rate + plan.mde_absolute

    control = rng.binomial(1, p_c, size=n)
    treatment = rng.binomial(1, p_t, size=n)

    row = {
        "count_c": n, "count_t": n,
        "mean_c": control.mean(), "mean_t": treatment.mean(),
    }
    result = stats_utils.two_proportion_test(
        row["count_c"], row["count_t"], row["mean_c"], row["mean_t"]
    )
    return {"plan": plan, "simulated_row": row, "test_result": result}
