# Phase 2 - Online Retail II Cleaning Report (real data)

Raw file: 1,067,371 rows.

| Step | Rows removed | % of raw |
|---|---|---|
| Exact duplicates | 34,335 | 3.22% |
| Junk / not-a-real-sale rows (bad debt, damaged, etc.) | 650 | 0.06% |
| Literal test entries (TEST001/TEST002) | 17 | 0.0% |

**Rows remaining after cleaning: 1,032,369**
(96.72% of the original file kept)

## The two output files

- `online_retail_all_clean.csv` - 1,032,369 rows. Use this
  for overall shop-level analysis (total revenue, top products, trends over
  time). Includes 234,507 rows with no
  customer_id (guest/wholesale orders) — as agreed, these are kept here.
- `online_retail_customer_clean.csv` - 797,862
  rows. Use this for anything about individual customers (churn, CLV, RFM).
  Only rows with a real customer_id are included.

## Other things worth knowing

- 19,100 rows are genuine returns/cancellations
  (negative quantity) — kept, as agreed, since they're real customer
  behaviour, not errors.
- 5,791 rows are non-merchandise charges
  (postage, bank charges, discounts, etc.) — kept in both files (they were
  real monetary events for that customer/order) but flagged with
  `is_product = False`, so any "best-selling product" analysis later can
  filter them out with one line of code.

## Open questions / notes
- DCGS* stock codes (~150 rows) kept as ordinary products - their exact meaning could not be confirmed from the data alone; negligible impact on any headline number either way.
