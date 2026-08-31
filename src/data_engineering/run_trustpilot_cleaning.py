"""
run_trustpilot_cleaning.py
----------------------------
Entry point for Phase 2 on the Trustpilot dataset. Run from the repo root:

    python -m src.data_engineering.run_trustpilot_cleaning
"""

from __future__ import annotations

import os

from . import trustpilot_loader, trustpilot_cleaning

PROCESSED_DIR = "data/processed"
REPORTS_DIR = "reports"


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("Loading raw file...")
    df_raw = trustpilot_loader.load_raw()

    print("Cleaning...")
    clean, report = trustpilot_cleaning.clean_trustpilot(df_raw)

    out_path = os.path.join(PROCESSED_DIR, "trustpilot_reviews_clean.csv")
    clean.to_csv(out_path, index=False)

    md = f"""# Phase 2 - Trustpilot Cleaning Report (real data)

Raw file: {report.rows_before:,} rows, {df_raw['company'].nunique():,} companies,
{df_raw['category'].nunique()} categories.

This dataset was already very clean (0 missing values, 0 duplicates found on
first inspection). Only 6 truly content-free rows existed out of 123,181 -
a length-based cutoff was deliberately NOT used, since hundreds of short but
genuine reviews (e.g. "Far too expensive") would have been wrongly removed.

| Removed | Rows |
|---|---|
| Exact duplicates | {report.duplicates_removed} |
| Phone-number-only reviews | {report.phone_number_rows_removed} |
| Punctuation-only reviews | {report.punctuation_only_rows_removed} |
| Non-English reviews | {report.non_english_rows_removed} |

**Rows remaining: {report.rows_after:,}** ({round(100*report.rows_after/report.rows_before,3)}% of raw kept)

Saved: `{out_path}`
"""
    with open(os.path.join(REPORTS_DIR, "trustpilot_cleaning_report.md"), "w") as f:
        f.write(md)

    print(md)


if __name__ == "__main__":
    main()
