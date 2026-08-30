"""
multiple_testing.py
--------------------
Every experiment in this dataset tests 4 metrics at once (and 13 of the 78
tests have more than one treatment arm). Evaluating "is p < 0.05" on each of
these independently inflates the false-positive rate across the collection -
exactly the trap Phase 4 of the project blueprint warns about. This module
applies Benjamini-Hochberg FDR correction across a chosen grouping and
reports how many "wins" survive correction.
"""

from __future__ import annotations

import pandas as pd
from statsmodels.stats.multitest import multipletests


def add_fdr_correction(df: pd.DataFrame, p_col: str = "p_value",
                        alpha: float = 0.05,
                        group_col: str | None = None) -> pd.DataFrame:
    """Add `p_adj` and `significant_adj` columns using Benjamini-Hochberg.

    group_col: if given, correction is applied separately within each group
    (e.g. per experiment_id, so one experiment's many metrics don't get
    penalised by another experiment's). If None, correction is applied
    across the whole dataframe at once (the stricter, "family-wise across
    the whole re-analysis" view). We report both perspectives in the main
    script because they answer different questions.
    """
    df = df.copy()

    def _correct(sub: pd.DataFrame) -> pd.DataFrame:
        reject, p_adj, _, _ = multipletests(sub[p_col], alpha=alpha, method="fdr_bh")
        sub = sub.copy()
        sub["p_adj"] = p_adj
        sub["significant_adj"] = reject
        return sub

    if group_col is None:
        return _correct(df)

    return df.groupby(group_col, group_keys=False).apply(_correct)


def summarise_significance(df: pd.DataFrame, p_col: str = "p_value",
                            p_adj_col: str = "p_adj",
                            alpha: float = 0.05) -> dict:
    n = len(df)
    n_sig_raw = int((df[p_col] < alpha).sum())
    n_sig_adj = int((df[p_adj_col] < alpha).sum()) if p_adj_col in df else None
    return {
        "n_tests": n,
        "pct_significant_raw": round(100 * n_sig_raw / n, 1) if n else None,
        "n_significant_raw": n_sig_raw,
        "pct_significant_fdr": round(100 * n_sig_adj / n, 1) if n_sig_adj is not None and n else None,
        "n_significant_fdr": n_sig_adj,
    }
