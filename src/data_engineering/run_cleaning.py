"""
run_cleaning.py
-----------------
Entry point for Phase 2 on Online Retail II. Run from the repo root:

    python -m src.data_engineering.run_cleaning

Reads data/raw/online_retail/online_retail_II.csv, cleans it per the rules
in online_retail_cleaning.py, writes two processed files and a plain-English
data quality report.
"""

from __future__ import annotations

import os

from . import online_retail_loader, online_retail_cleaning

PROCESSED_DIR = "data/processed"
REPORTS_DIR = "reports"


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("Loading raw file...")
    df_raw = online_retail_loader.load_raw()

    print("Cleaning...")
    all_clean, customer_clean, report = online_retail_cleaning.clean_online_retail(df_raw)

    all_path = os.path.join(PROCESSED_DIR, "online_retail_all_clean.csv")
    cust_path = os.path.join(PROCESSED_DIR, "online_retail_customer_clean.csv")
    all_clean.to_csv(all_path, index=False)
    customer_clean.to_csv(cust_path, index=False)

    pct = lambda n, d: round(100 * n / d, 2) if d else None

    md = f"""# Phase 2 - Online Retail II Cleaning Report (real data)

Raw file: {report.rows_before:,} rows.

| Step | Rows removed | % of raw |
|---|---|---|
| Exact duplicates | {report.duplicates_removed:,} | {pct(report.duplicates_removed, report.rows_before)}% |
| Junk / not-a-real-sale rows (bad debt, damaged, etc.) | {report.junk_rows_removed:,} | {pct(report.junk_rows_removed, report.rows_before)}% |
| Literal test entries (TEST001/TEST002) | {report.test_rows_removed:,} | {pct(report.test_rows_removed, report.rows_before)}% |

**Rows remaining after cleaning: {report.rows_after_all:,}**
({pct(report.rows_after_all, report.rows_before)}% of the original file kept)

## The two output files

- `online_retail_all_clean.csv` - {report.rows_after_all:,} rows. Use this
  for overall shop-level analysis (total revenue, top products, trends over
  time). Includes {report.rows_missing_customer_id:,} rows with no
  customer_id (guest/wholesale orders) — as agreed, these are kept here.
- `online_retail_customer_clean.csv` - {report.rows_after_customer_level:,}
  rows. Use this for anything about individual customers (churn, CLV, RFM).
  Only rows with a real customer_id are included.

## Other things worth knowing

- {report.cancellation_rows_kept:,} rows are genuine returns/cancellations
  (negative quantity) — kept, as agreed, since they're real customer
  behaviour, not errors.
- {report.non_product_rows_flagged:,} rows are non-merchandise charges
  (postage, bank charges, discounts, etc.) — kept in both files (they were
  real monetary events for that customer/order) but flagged with
  `is_product = False`, so any "best-selling product" analysis later can
  filter them out with one line of code.

## Open questions / notes
{chr(10).join('- ' + n for n in report.notes)}
"""
    with open(os.path.join(REPORTS_DIR, "online_retail_cleaning_report.md"), "w") as f:
        f.write(md)

    print(md)
    print(f"Saved: {all_path}, {cust_path}")


if __name__ == "__main__":
    main()
