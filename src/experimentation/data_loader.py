"""
data_loader.py
---------------
Loads the ASOS Digital Experiments Dataset (Liu et al., 2021) and prepares it
for re-analysis.

Source: https://osf.io/64jsb/
Schema (one row = one snapshot of one variant-vs-control comparison, for one
metric, at one point in time since the experiment started):

    experiment_id     : anonymised experiment identifier (str)
    variant_id        : id of the TREATMENT arm being compared to control (int)
    metric_id         : 1-4, the organisational decision metric (int)
    time_since_start  : days since the experiment started (float)
    count_c, count_t  : sample size in control / treatment at this snapshot
    mean_c, mean_t    : sample mean of the metric in control / treatment
    variance_c/t      : sample variance in control / treatment (may be NaN)

Important notes we discovered by profiling the real file (not assumed from
the paper alone):
    - metric_id == 1 is a Bernoulli/proportion metric: variance_c is always
      (to floating point precision) equal to mean_c * (1 - mean_c). It is
      never missing.
    - metric_id in {2, 3, 4} are real-valued/count metrics. Their variance
      columns are given directly, and are missing (NaN) in ~4.3% of rows.
      We drop those rows for the affected metric rather than impute, since
      a fabricated variance would silently corrupt every downstream p-value.
"""

from __future__ import annotations

import pandas as pd

RAW_PATH = "data/raw/asos/asos_digital_experiments_dataset.csv"

BINARY_METRIC_IDS = {1}
CONTINUOUS_METRIC_IDS = {2, 3, 4}


def load_raw(path: str = RAW_PATH) -> pd.DataFrame:
    """Load the raw CSV exactly as published, with dtypes fixed."""
    df = pd.read_csv(path)
    df["experiment_id"] = df["experiment_id"].astype(str)
    for col in ["variant_id", "metric_id"]:
        df[col] = df[col].astype(int)
    return df


def classify_metric_type(metric_id: int) -> str:
    if metric_id in BINARY_METRIC_IDS:
        return "binary"
    if metric_id in CONTINUOUS_METRIC_IDS:
        return "continuous"
    raise ValueError(f"Unrecognised metric_id: {metric_id}")


def add_metric_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["metric_type"] = df["metric_id"].map(classify_metric_type)
    return df


def drop_rows_with_missing_variance(df: pd.DataFrame) -> pd.DataFrame:
    """Continuous metrics occasionally have NaN variance. We exclude those
    specific rows and log how many were dropped, rather than imputing."""
    before = len(df)
    mask_bad = df["metric_type"].eq("continuous") & (
        df["variance_c"].isna() | df["variance_t"].isna()
    )
    dropped = int(mask_bad.sum())
    df = df.loc[~mask_bad].copy()
    if dropped:
        print(f"[data_loader] dropped {dropped}/{before} rows "
              f"({dropped/before:.2%}) with missing variance on a "
              f"continuous metric")
    return df


def drop_zero_count_rows(df: pd.DataFrame) -> pd.DataFrame:
    """A small number of rows (8 in the published file) have count_c == 0 or
    count_t == 0 - almost certainly a snapshot logged before that arm had
    accrued any samples. These break every variance/rate calculation and
    carry no usable information, so we drop them and log it. This is a real
    data-quality finding, not a hypothetical one - worth stating as such in
    a Phase 1 data quality write-up."""
    before = len(df)
    mask_bad = (df["count_c"] == 0) | (df["count_t"] == 0)
    dropped = int(mask_bad.sum())
    df = df.loc[~mask_bad].copy()
    if dropped:
        print(f"[data_loader] dropped {dropped}/{before} rows with "
              f"count_c == 0 or count_t == 0 (zero-sample snapshots)")
    return df


def get_final_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce the time series to one row per (experiment_id, variant_id,
    metric_id): the LAST snapshot recorded, i.e. the experiment's concluding
    result. This is what a re-analysis of "the 78 completed tests" should
    use as the headline result; the full time series is used separately
    for the heterogeneity/novelty-effect check.
    """
    idx = (
        df.groupby(["experiment_id", "variant_id", "metric_id"])[
            "time_since_start"
        ].idxmax()
    )
    return df.loc[idx].reset_index(drop=True)


def load_final_results(path: str = RAW_PATH) -> pd.DataFrame:
    """Convenience one-shot loader used by the main analysis script."""
    df = load_raw(path)
    df = add_metric_type(df)
    df = drop_rows_with_missing_variance(df)
    df = drop_zero_count_rows(df)
    return get_final_snapshot(df)
