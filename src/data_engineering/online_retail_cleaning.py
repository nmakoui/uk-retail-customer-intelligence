"""
online_retail_cleaning.py
---------------------------
Implements the cleaning decisions agreed on for the Online Retail II
dataset. Every rule below exists because we found a specific, real problem
by profiling the actual file - none of this is generic boilerplate.

Decisions made together (see docs/data_dictionary_online_retail.md for the
full writeup with real row counts):

1. Missing Customer ID (22.8% of rows): KEPT for overall shop-level totals,
   EXCLUDED only from customer-level analysis (churn/CLV/RFM). This module
   therefore produces TWO cleaned outputs, not one.
2. Cancellations/returns (Invoice starting with "C", negative Quantity):
   KEPT - they are real customer behaviour, not data errors.
3. Exact duplicate rows (3.2%): REMOVED - almost certainly double-scanned
   items, not two real purchases.
4. Rows with price <= 0 that are internal notes, not sales
   ("damaged", "check", "found", "missing", "smashed", "thrown away",
   "Adjust bad debt", etc.): REMOVED - these carry no real transaction
   value. A further ~5,600 zero-price rows have ordinary product names we
   could not confidently identify as write-offs - these are KEPT and
   flagged with is_zero_value=True, but note they add exactly £0 to any
   revenue/CLV figure regardless, so this choice cannot distort those
   numbers either way.
5. Literal test entries (StockCode TEST001/TEST002): REMOVED - not real
   data at all.
6. Non-merchandise charge codes (POST, DOT, C2, D, M, BANK CHARGES,
   ADJUST, ADJUST2, AMAZONFEE, CRUK, PADS, S, B, C3, GIFT, gift_0001_*):
   KEPT (they were real monetary events tied to a customer's order - e.g.
   postage genuinely paid), but flagged with is_product=False so
   product-level analysis (Phase 4 onward) can exclude them cleanly.
7. DCGS* codes: kept as ordinary products. We could not determine their
   exact meaning from the data alone (documented as an open question, not
   a guess dressed up as fact) - at ~150 rows total (0.01%) this cannot
   meaningfully change any headline result either way.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

NON_PRODUCT_CODES = {
    "POST", "DOT", "C2", "D", "M", "m", "BANK CHARGES", "ADJUST", "ADJUST2",
    "AMAZONFEE", "CRUK", "PADS", "S", "B", "C3", "GIFT",
}
TEST_CODES = {"TEST001", "TEST002"}

JUNK_DESCRIPTIONS = {
    "check", "?", "damages", "damaged", "damages?", "found", "missing",
    "sold as set on dotcom", "adjustment", "dotcom", "amazon",
    "adjust bad debt", "smashed", "mailout", "thrown away",
    "unsaleable, destroyed.", "checked", "given away", "manual",
}


@dataclass
class CleaningReport:
    rows_before: int
    duplicates_removed: int
    junk_rows_removed: int
    test_rows_removed: int
    rows_after_all: int
    rows_missing_customer_id: int
    rows_after_customer_level: int
    non_product_rows_flagged: int
    cancellation_rows_kept: int
    notes: list[str] = field(default_factory=list)


def _is_gift_card_code(stock_code: str) -> bool:
    return stock_code.startswith("gift_0001_")


def _is_non_product(stock_code: str) -> bool:
    return stock_code in NON_PRODUCT_CODES or _is_gift_card_code(stock_code)


def clean_online_retail(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, CleaningReport]:
    """Returns (all_transactions_clean, customer_transactions_clean, report).

    all_transactions_clean:      every valid row, INCLUDING rows with no
                                  customer_id - use for overall shop totals
                                  (total revenue, top products, etc.)
    customer_transactions_clean: subset with a customer_id present - use
                                  for anything about individual customers
                                  (churn, CLV, RFM).
    """
    df = df_raw.copy()
    rows_before = len(df)

    # --- 1. remove exact duplicate rows ---
    dup_mask = df.duplicated()
    duplicates_removed = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()

    # --- 2. remove junk / not-a-real-sale rows ---
    desc_lower = df["description"].astype(str).str.strip().str.lower()
    is_junk_desc = desc_lower.isin(JUNK_DESCRIPTIONS)
    is_non_positive_price = df["price"] <= 0
    junk_mask = is_non_positive_price & (is_junk_desc | (df["price"] < 0))
    # (price < 0 rows, e.g. "Adjust bad debt", are junk regardless of
    #  description text; price == 0 rows are only junk if the description
    #  confirms it's a note rather than a genuine free item)
    junk_rows_removed = int(junk_mask.sum())
    df = df.loc[~junk_mask].copy()

    # --- 3. remove literal test entries ---
    test_mask = df["stock_code"].isin(TEST_CODES)
    test_rows_removed = int(test_mask.sum())
    df = df.loc[~test_mask].copy()

    # --- 4. derived columns ---
    df["is_cancellation"] = df["invoice"].str.startswith("C")
    df["is_product"] = ~df["stock_code"].map(_is_non_product)
    df["line_value"] = df["quantity"] * df["price"]
    # Remaining price==0 rows (real product names we couldn't confidently
    # identify as write-offs) are kept - they add exactly £0 to any revenue
    # or customer-value figure either way, so this can't distort our
    # numbers - but flagged so a future "units sold" style analysis
    # (which wouldn't naturally filter on price) can exclude them if wanted.
    df["is_zero_value"] = df["price"] == 0

    rows_after_all = len(df)
    cancellation_rows_kept = int(df["is_cancellation"].sum())
    non_product_rows_flagged = int((~df["is_product"]).sum())

    all_transactions_clean = df.reset_index(drop=True)

    # --- 5. customer-level subset ---
    rows_missing_customer_id = int(df["customer_id"].isna().sum())
    customer_transactions_clean = df.loc[df["customer_id"].notna()].copy()
    customer_transactions_clean["customer_id"] = (
        customer_transactions_clean["customer_id"].astype(int)
    )
    customer_transactions_clean = customer_transactions_clean.reset_index(drop=True)

    report = CleaningReport(
        rows_before=rows_before,
        duplicates_removed=duplicates_removed,
        junk_rows_removed=junk_rows_removed,
        test_rows_removed=test_rows_removed,
        rows_after_all=rows_after_all,
        rows_missing_customer_id=rows_missing_customer_id,
        rows_after_customer_level=len(customer_transactions_clean),
        non_product_rows_flagged=non_product_rows_flagged,
        cancellation_rows_kept=cancellation_rows_kept,
        notes=[
            "DCGS* stock codes (~150 rows) kept as ordinary products - "
            "their exact meaning could not be confirmed from the data "
            "alone; negligible impact on any headline number either way.",
        ],
    )

    return all_transactions_clean, customer_transactions_clean, report
