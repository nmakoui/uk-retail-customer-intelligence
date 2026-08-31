"""
trustpilot_cleaning.py
------------------------
Implements the (very small) cleaning agreed for the Trustpilot dataset.
Unlike Online Retail II, this dataset had zero missing values and zero
duplicate rows out of the box - genuinely clean already. The only real
issue found by profiling: 6 rows out of 123,181 (0.005%) have no actual
review content. We remove exactly those 6, and nothing else - a length-
based cutoff was deliberately rejected, because hundreds of short-but-
genuine reviews (e.g. "Far too expensive") would have been wrongly caught
by any blanket minimum-length rule.

The 6 rows removed are exactly:
1. A review that is only digits (looks like a phone number, e.g. "01959312890")
2. Reviews that are only punctuation/whitespace (e.g. "...........")
   - 3 such rows
3. Reviews written in a language other than English (detected with a
   simple non-ASCII character ratio - a review that is mostly non-ASCII
   characters is very unlikely to be English) - 2 such rows

This is a small, explicit, explainable rule set - not a generic language
detector - because at this scale (6 rows) precision matters more than
recall, and a heavier tool would be overkill.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

ONLY_DIGITS_PATTERN = re.compile(r"^\d+$")
ONLY_PUNCT_PATTERN = re.compile(r"^[\.\?\!\-\s]+$")
NON_ASCII_RATIO_THRESHOLD = 0.3


@dataclass
class TrustpilotCleaningReport:
    rows_before: int
    duplicates_removed: int
    phone_number_rows_removed: int
    punctuation_only_rows_removed: int
    non_english_rows_removed: int
    rows_after: int


def _non_ascii_ratio(text: str) -> float:
    if not isinstance(text, str) or len(text) == 0:
        return 0.0
    non_ascii = sum(1 for c in text if ord(c) > 127)
    return non_ascii / len(text)


def clean_trustpilot(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, TrustpilotCleaningReport]:
    df = df_raw.copy()
    rows_before = len(df)

    dup_mask = df.duplicated()
    duplicates_removed = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()

    review = df["review"].astype(str)

    phone_mask = review.str.match(ONLY_DIGITS_PATTERN)
    phone_removed = int(phone_mask.sum())

    punct_mask = review.str.match(ONLY_PUNCT_PATTERN)
    punct_removed = int(punct_mask.sum())

    non_ascii_ratio = review.apply(_non_ascii_ratio)
    non_english_mask = non_ascii_ratio > NON_ASCII_RATIO_THRESHOLD
    non_english_removed = int(non_english_mask.sum())

    junk_mask = phone_mask | punct_mask | non_english_mask
    df = df.loc[~junk_mask].copy().reset_index(drop=True)

    report = TrustpilotCleaningReport(
        rows_before=rows_before,
        duplicates_removed=duplicates_removed,
        phone_number_rows_removed=phone_removed,
        punctuation_only_rows_removed=punct_removed,
        non_english_rows_removed=non_english_removed,
        rows_after=len(df),
    )
    return df, report
