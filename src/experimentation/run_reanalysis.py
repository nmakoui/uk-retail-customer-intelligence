"""
run_reanalysis.py
------------------
Entry point for Phase 8a + 8b. Run from the repo root:

    python -m src.experimentation.run_reanalysis

Produces:
    reports/asos_reanalysis_summary.csv   - one row per test, with effect,
                                             CI, raw p-value, BH-adjusted p
    reports/figures/pvalue_histogram.png  - distribution of raw p-values
    reports/figures/heterogeneity_examples.png
    A printed summary (also written to reports/asos_reanalysis_report.md)
    covering: % significant before/after correction, comparison to the
    ~25%-of-tests-significant benchmark widely cited for this dataset, and
    the Phase 8b power-analysis + simulated-experiment walkthrough.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from . import data_loader, stats_utils, multiple_testing, heterogeneity, power_analysis

REPORTS_DIR = "reports"
FIGS_DIR = os.path.join(REPORTS_DIR, "figures")


def run_final_snapshot_analysis() -> pd.DataFrame:
    final = data_loader.load_final_results()

    results = final.apply(stats_utils.run_test, axis=1)
    final = final.copy()
    final["abs_effect"] = [r.abs_effect for r in results]
    final["rel_effect"] = [r.rel_effect for r in results]
    final["se"] = [r.se for r in results]
    final["z"] = [r.z for r in results]
    final["p_value"] = [r.p_value for r in results]
    final["ci_low"] = [r.ci_low for r in results]
    final["ci_high"] = [r.ci_high for r in results]

    # Two views of multiple-testing correction, as flagged in multiple_testing.py:
    final_within = multiple_testing.add_fdr_correction(
        final, group_col="experiment_id")
    final_within = final_within.rename(columns={"p_adj": "p_adj_within_experiment",
                                                 "significant_adj": "significant_within_experiment"})

    final_across = multiple_testing.add_fdr_correction(final, group_col=None)
    final["p_adj_across_all_tests"] = final_across["p_adj"]
    final["significant_across_all_tests"] = final_across["significant_adj"]
    final["p_adj_within_experiment"] = final_within["p_adj_within_experiment"]
    final["significant_within_experiment"] = final_within["significant_within_experiment"]

    return final


def plot_pvalue_histogram(final: pd.DataFrame, path: str):
    plt.figure(figsize=(7, 4.5))
    plt.hist(final["p_value"], bins=20, edgecolor="black")
    plt.axvline(0.05, color="red", linestyle="--", label="alpha = 0.05")
    plt.xlabel("raw p-value")
    plt.ylabel("number of test snapshots")
    plt.title("Distribution of raw p-values across all ASOS test/metric/variant\ncombinations (final snapshot)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_heterogeneity_examples(df_ts: pd.DataFrame, unstable: pd.DataFrame, path: str, n_examples: int = 4):
    picks = unstable.sort_values("n_snapshots", ascending=False).head(n_examples)
    if picks.empty:
        return
    fig, axes = plt.subplots(1, len(picks), figsize=(4 * len(picks), 3.5), squeeze=False)
    for ax, (_, row) in zip(axes[0], picks.iterrows()):
        series = df_ts[
            (df_ts.experiment_id == row.experiment_id) &
            (df_ts.variant_id == row.variant_id) &
            (df_ts.metric_id == row.metric_id)
        ].sort_values("time_since_start")
        ax.plot(series["time_since_start"], series["abs_effect"], marker="o", ms=3)
        ax.axhline(0, color="grey", linewidth=0.8)
        ax.set_title(f"exp {row.experiment_id[:6]} m{row.metric_id} v{row.variant_id}", fontsize=9)
        ax.set_xlabel("days since start")
    axes[0][0].set_ylabel("absolute effect (treatment - control)")
    fig.suptitle("Effect size over time - examples flagged as unstable")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_phase8b_example() -> str:
    plan = power_analysis.required_sample_size(
        baseline_rate=0.12, mde_absolute=0.012, alpha=0.05, power=0.8
    )
    sim = power_analysis.simulate_experiment(plan)
    r = sim["test_result"]
    return (
        f"### Phase 8b - designing a new (SIMULATED) retention experiment\n\n"
        f"Scenario: a retention email sent to customers flagged high-churn-risk. "
        f"Primary metric: repeat purchase within 30 days.\n\n"
        f"- Assumed baseline repeat-purchase rate: {plan.baseline_rate:.1%}\n"
        f"- Minimum detectable absolute effect: {plan.mde_absolute:.1%} "
        f"(baseline -> {plan.baseline_rate + plan.mde_absolute:.1%})\n"
        f"- alpha = {plan.alpha}, power = {plan.power}\n"
        f"- **Required sample size: {plan.required_n_per_arm:,} customers per arm "
        f"({plan.total_required_n:,} total)**\n\n"
        f"Simulated run (synthetic data, NOT observed) assuming the true "
        f"effect equals the planned MDE:\n"
        f"- control rate: {r.mean_c:.4f}, treatment rate: {r.mean_t:.4f}\n"
        f"- observed effect: {r.abs_effect:+.4f} "
        f"(95% CI [{r.ci_low:+.4f}, {r.ci_high:+.4f}])\n"
        f"- p-value: {r.p_value:.4g}\n"
    )


def main():
    os.makedirs(FIGS_DIR, exist_ok=True)

    # --- Phase 8a: re-analysis of the 78 real ASOS experiments ---
    final = run_final_snapshot_analysis()
    final.to_csv(os.path.join(REPORTS_DIR, "asos_reanalysis_summary.csv"), index=False)

    summary_raw_vs_within = multiple_testing.summarise_significance(
        final, p_adj_col="p_adj_within_experiment")
    summary_raw_vs_across = multiple_testing.summarise_significance(
        final, p_adj_col="p_adj_across_all_tests")

    plot_pvalue_histogram(final, os.path.join(FIGS_DIR, "pvalue_histogram.png"))

    # heterogeneity / novelty-effect check (needs full time series, not just final snapshot)
    raw = data_loader.load_raw()
    raw = data_loader.add_metric_type(raw)
    raw = data_loader.drop_rows_with_missing_variance(raw)
    raw = data_loader.drop_zero_count_rows(raw)
    ts = heterogeneity.build_effect_timeseries(raw)
    unstable = heterogeneity.flag_unstable_series(ts)

    # A sign flip is only a meaningful "instability" story for tests whose
    # FINAL result was actually significant - for a near-null effect,
    # signs wobble around zero from noise alone, and flagging that as
    # "novelty effect" would be a methodological overreach, not a finding.
    sig_keys = final.loc[final["p_value"] < 0.05,
                          ["experiment_id", "variant_id", "metric_id"]]
    unstable_on_sig = unstable.merge(sig_keys, on=["experiment_id", "variant_id", "metric_id"])
    n_unstable = int(unstable_on_sig["sign_flip_after_early_period"].sum())
    n_checked = len(unstable_on_sig)
    n_unstable_all = int(unstable["sign_flip_after_early_period"].sum())
    n_checked_all = len(unstable)

    plot_heterogeneity_examples(
        ts, unstable_on_sig[unstable_on_sig.sign_flip_after_early_period],
        os.path.join(FIGS_DIR, "heterogeneity_examples.png"))

    phase8b_text = run_phase8b_example()

    report = f"""# Phase 8 - ASOS Experimentation Re-analysis (real data, computed on {pd.Timestamp.today().date()})

Dataset: ASOS Digital Experiments Dataset (Liu et al., 2021), 78 real experiments,
{final.shape[0]} test/metric/variant combinations at their final recorded snapshot.

## 8a. Headline results

- Raw significance (p < 0.05), no correction: **{summary_raw_vs_across['n_significant_raw']}
  / {summary_raw_vs_across['n_tests']} ({summary_raw_vs_across['pct_significant_raw']}%)**
- After Benjamini-Hochberg correction, **within each experiment's own 4 metrics**:
  {summary_raw_vs_within['n_significant_fdr']} / {summary_raw_vs_within['n_tests']}
  ({summary_raw_vs_within['pct_significant_fdr']}%) remain significant
- After Benjamini-Hochberg correction, **across all {summary_raw_vs_across['n_tests']}
  tests in the dataset at once** (the stricter view):
  {summary_raw_vs_across['n_significant_fdr']} / {summary_raw_vs_across['n_tests']}
  ({summary_raw_vs_across['pct_significant_fdr']}%) remain significant

This gives us a real number to compare against the commonly cited rule of thumb
that roughly a quarter of online experiments show a statistically significant
result - useful context to quote and interpret carefully in a portfolio write-up,
not to over-claim from.

## Effect-stability check (novelty/primacy effect proxy)

Restricted to tests whose **final result was statistically significant**
(instability on a near-null effect is just noise wobbling around zero, not a
finding - checked separately below): of **{n_checked}** significant
test/metric/variant series with at least 5 snapshots, **{n_unstable}** show
the effect's sign flipping after the first 20% of the observed run, i.e. the
concluding "winning" or "losing" call was not yet stable for a meaningful
part of the test.

For context, across *all* {n_checked_all} series regardless of significance,
{n_unstable_all} show a sign flip - much higher, exactly because most of
those are near-null effects where sign is meaningless noise. That contrast
is itself worth stating explicitly in a write-up: it is the difference
between a real methodological check and a spurious one.

See `figures/heterogeneity_examples.png` for the most heavily-monitored
significant examples. This remains a simple, explainable heuristic, not a
formal change-point test.

{phase8b_text}

## Files produced
- `reports/asos_reanalysis_summary.csv` - full per-test results (effect, CI, raw p,
  both BH-adjusted p variants)
- `reports/figures/pvalue_histogram.png`
- `reports/figures/heterogeneity_examples.png`
"""
    with open(os.path.join(REPORTS_DIR, "asos_reanalysis_report.md"), "w") as f:
        f.write(report)

    print(report)


if __name__ == "__main__":
    main()
