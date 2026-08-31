# Data Dictionary — Online Retail II

Source: UCI ML Repository (ID 502) / Kaggle mirror `mashlyn/online-retail-ii-uci`.
Real transactions from a UK-registered, non-store online retailer selling
giftware, December 2009 – December 2011.

## Raw schema

| Column | Type | Description |
|---|---|---|
| `Invoice` | string | Order number. Starts with "C" if it's a cancellation/return |
| `StockCode` | string | Product code |
| `Description` | string | Product name |
| `Quantity` | integer | Units bought (negative = returned) |
| `InvoiceDate` | datetime | When the order line was recorded |
| `Price` | float | Price per unit, in GBP |
| `Customer ID` | float (nullable) | Customer identifier - missing for guest/wholesale orders |
| `Country` | string | Customer's country |

## Profiling findings (from actually running the data)

- **1,067,371 raw rows**, 53,628 orders, 5,942 identified customers, 5,305
  distinct product codes, spanning exactly 2 years.
- **92% of rows are from the UK**; the remaining 8% span 42 other
  countries (mostly nearby Europe).
- **22.8% of rows (243,007) have no Customer ID.** These look like guest
  checkouts or wholesale orders never linked to an account.
- **1.8% of rows (19,494) are cancellations/returns** (Invoice starts with
  "C", Quantity is negative) — genuine customer behaviour, not an error.
- **3.2% of rows (34,335) are exact duplicates** — same invoice, product,
  price, quantity, customer, everything. Almost certainly items scanned
  twice by mistake.
- **6,207 rows (0.58%) have price ≤ 0** and are not real sales: 5 are
  "Adjust bad debt" accounting write-offs (negative price, no customer),
  and ~650 more have descriptions that are clearly internal notes
  ("damaged", "check", "smashed", "thrown away", "unsaleable, destroyed.",
  etc.). A further ~5,600 rows are priced at exactly £0 with ordinary
  product names we couldn't confidently identify as write-offs - these
  add exactly £0 to any revenue/CLV figure regardless of how they're
  handled, so we kept them and flagged them (`is_zero_value`) rather than
  guess.
- **17 rows use literal test stock codes** (`TEST001`, `TEST002`) - not
  real data.
- **6,076 rows (0.57%) use a non-merchandise stock code**: `POST`/`DOT`/
  `C2` (postage/carriage), `D` (discount), `M` (manual entry),
  `BANK CHARGES`, `ADJUST`/`ADJUST2`, `AMAZONFEE`, `CRUK` (charity
  donation), `PADS`, `S` (samples), `B` (bad debt marker), `GIFT`/
  `gift_0001_*` (real gift vouchers, confirmed by their descriptions -
  e.g. "Dotcomgiftshop Gift Voucher £20.00"). These are real monetary
  events tied to a customer's order, so they're kept, but flagged
  `is_product = False` so product-level analysis can exclude them.
- **~150 rows use `DCGS*` codes** whose exact meaning we could not confirm
  from the data alone - kept as ordinary products; too small a count
  (0.01%) to meaningfully affect any headline result either way.

## Decisions made together (see chat history / project log for full reasoning)

| Issue | Decision |
|---|---|
| Missing Customer ID | Kept for shop-wide totals; excluded only from customer-level analysis |
| Cancellations/returns | Kept - genuine customer behaviour |
| Exact duplicates | Removed |
| Bad-debt / write-off / test rows | Removed |
| Non-merchandise charge codes | Kept, flagged `is_product = False` |
| Ambiguous zero-price product rows | Kept, flagged `is_zero_value = True` (zero revenue impact either way) |

## Output files

- `data/processed/online_retail_all_clean.csv` — 1,032,369 rows. Use for
  shop-wide analysis.
- `data/processed/online_retail_customer_clean.csv` — 797,862 rows
  (customer_id always present). Use for churn/CLV/RFM work.

Both add these columns beyond the raw schema: `is_cancellation`,
`is_product`, `is_zero_value`, `line_value` (= quantity × price).
