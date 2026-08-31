# Data Dictionary — Trustpilot Reviews 123k

Source: Kaggle `jerassy/trustpilot-reviews-123k` (MIT licensed). 123,181
English-language UK Trustpilot reviews, 1,680 companies, 22 categories,
collected Dec 2024–Jan 2025.

## Raw schema

| Column | Type | Description |
|---|---|---|
| `category` | string | One of 22 business categories (e.g. "Shopping & Fashion") |
| `company` | string | Company domain (e.g. `example.co.uk`) |
| `description` | string | The company's own Trustpilot profile description - identical across every review row for that company (expected, not an error) |
| `title` | string | Review headline |
| `review` | string | Review body |
| `stars` | integer 1-5 | Star rating |

## Profiling findings (from actually running the data)

- **123,181 rows, 1,680 companies, 22 categories.** A simple `wc -l` on the
  raw file reports 840,017 lines - much higher than the real row count -
  because many reviews contain literal line breaks inside quoted CSV
  fields. Always load with a proper CSV parser, not a line count, to
  check size.
- **Zero missing values, zero duplicate rows** on first inspection -
  genuinely clean already, unusual for a real-world dataset.
- **Confirmed UK-focused**: 578 companies use `.co.uk` domains directly;
  most `.com`/other-TLD companies in the sample are also clearly UK
  businesses by name (`canadianaffair.com`, `ukchristmasworld.com`, etc.)
- **Star ratings are reasonably balanced**: 24,065 one-star, 19,687
  two-star, 21,264 three-star, 26,013 four-star, 32,152 five-star.
- **No encoding/mojibake issues found** (unlike the `Â£` symbols seen in
  Online Retail II).
- **Review length**: median 290 characters, ranges from 10 to ~9,956.
  Short reviews (e.g. "Far too expensive", "Simple to enter") are
  overwhelmingly genuine opinions, not junk - a blanket minimum-length
  filter would have wrongly discarded hundreds of real reviews to catch
  a handful of bad ones, so none was applied.
- **Only 6 rows (0.005%) had no real content**: 1 review that was only a
  phone number, 3 that were only punctuation/dots, and 2 written in a
  non-English language (detected via a simple non-ASCII character ratio).

## Decision made together

Remove exactly those 6 content-free rows; keep everything else, including
all short-but-genuine reviews.

## Output file

`data/processed/trustpilot_reviews_clean.csv` — 123,175 rows.
