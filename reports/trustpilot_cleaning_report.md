# Phase 2 - Trustpilot Cleaning Report (real data)

Raw file: 123,181 rows, 1,680 companies,
22 categories.

This dataset was already very clean (0 missing values, 0 duplicates found on
first inspection). Only 6 truly content-free rows existed out of 123,181 -
a length-based cutoff was deliberately NOT used, since hundreds of short but
genuine reviews (e.g. "Far too expensive") would have been wrongly removed.

| Removed | Rows |
|---|---|
| Exact duplicates | 0 |
| Phone-number-only reviews | 1 |
| Punctuation-only reviews | 3 |
| Non-English reviews | 2 |

**Rows remaining: 123,175** (99.995% of raw kept)

Saved: `data/processed\trustpilot_reviews_clean.csv`
