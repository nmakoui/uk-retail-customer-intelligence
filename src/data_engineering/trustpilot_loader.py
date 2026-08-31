"""
trustpilot_loader.py
----------------------
Loads the raw Trustpilot Reviews 123k dataset (Kaggle: jerassy/trustpilot-
reviews-123k, MIT licensed). 123,181 UK Trustpilot reviews across 1,680
companies and 22 categories.

Raw columns: category, company, description, title, review, stars

No cleaning decisions happen here - see trustpilot_cleaning.py for that.
"""

from __future__ import annotations

import pandas as pd

RAW_PATH = "data/raw/trustpilot/trustpilot_reviews_2005.csv"


def load_raw(path: str = RAW_PATH) -> pd.DataFrame:
    """Load the raw CSV exactly as published. pandas' default C parser
    handles the multi-line review/description text fields correctly as
    long as they're properly quoted in the source file (they are here) -
    a plain line-count of the file will look much bigger than the real
    row count for exactly this reason, which is worth knowing if you ever
    sanity-check file size with `wc -l` before loading it."""
    df = pd.read_csv(path)
    return df
