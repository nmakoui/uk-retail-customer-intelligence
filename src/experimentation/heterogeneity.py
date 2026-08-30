"""
heterogeneity.py
-----------------
The final-snapshot re-analysis (stats_utils + multiple_testing) answers
"what was the concluding result". It cannot tell you whether that result
was stable throughout the test or whether it was still drifting when the
company stopped it - a classic "novelty/primacy effect" concern in
experimentation. This module uses the FULL time series (not just the final
snapshot) to check that.

For each (experiment_id, variant_id, metric_id) series with more than one
snapshot, we compute the relative effect at every time point and flag a
series as "unstable" if either:
  (a) the sign of the effect flips at least once after the first 20% of
      the observed duration, or
  (b) the relative effect at the final snapshot differs from the relative
      effect at the midpoint by more than `drift_threshold` (default 50%
      of the final effect's own magnitude).
These are simple, explainable heuristics - not a claim of causal novelty
detection - and are reported as such.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import stats_utils


def build_effect_timeseries(df_full: pd.DataFrame) -> pd.DataFrame:
    """df_full must still contain all snapshots (i.e. NOT reduced to the
    final one) and already have `metric_type` attached.

    Implemented as an explicit loop over groups (rather than
    groupby().apply()) because recent pandas versions (2.2+) exclude the
    grouping columns from the sub-frame passed into apply by default,
    which would silently drop experiment_id/variant_id/metric_id here -
    exactly the kind of quiet breakage worth avoiding in a pipeline whose
    output feeds a "which experiment was unstable" report.
    """
    keys = ["experiment_id", "variant_id", "metric_id"]
    chunks = []
    for _, group in df_full.groupby(keys):
        group = group.sort_values("time_since_start").reset_index(drop=True)
        effects = [stats_utils.run_test(row).abs_effect for _, row in group.iterrows()]
        group = group.copy()
        group["abs_effect"] = effects
        chunks.append(group)
    return pd.concat(chunks, ignore_index=True)


def flag_unstable_series(df_ts: pd.DataFrame,
                          min_snapshots: int = 5,
                          drift_threshold: float = 0.5) -> pd.DataFrame:
    """Returns one row per (experiment_id, variant_id, metric_id) with a
    boolean `sign_flip` and `large_drift` flag plus supporting numbers."""
    records = []
    keys = ["experiment_id", "variant_id", "metric_id"]
    for key, group in df_ts.groupby(keys):
        group = group.sort_values("time_since_start")
        if len(group) < min_snapshots:
            continue

        cutoff_idx = max(1, int(0.2 * len(group)))
        late = group.iloc[cutoff_idx:]
        signs = np.sign(late["abs_effect"])
        signs_nonzero = signs[signs != 0]
        sign_flip = signs_nonzero.nunique() > 1 if len(signs_nonzero) else False

        final_effect = group["abs_effect"].iloc[-1]
        mid_effect = group["abs_effect"].iloc[len(group) // 2]
        denom = abs(final_effect) if final_effect != 0 else np.nan
        drift = abs(final_effect - mid_effect) / denom if denom else np.nan
        large_drift = bool(drift is not np.nan and drift > drift_threshold)

        records.append({
            "experiment_id": key[0], "variant_id": key[1], "metric_id": key[2],
            "n_snapshots": len(group),
            "final_effect": final_effect,
            "mid_effect": mid_effect,
            "sign_flip_after_early_period": bool(sign_flip),
            "large_drift_mid_to_final": large_drift,
        })
    return pd.DataFrame(records)
