# Impact Log

Honest, demonstrable metrics only — see the project blueprint's rule:
never invent revenue/conversion impact the data can't support.

## Phase 2 — Get, inspect, and clean the data

### Online Retail II

**Task:** inspect and clean the real Online Retail II transaction file,
following decisions made together on how to handle missing customer IDs,
returns, and duplicates.

- Rows processed: 1,067,371 raw → 1,032,369 after cleaning (96.7% kept).
- Removed: 34,335 exact duplicates, 650 internal write-off/note rows, 17
  literal test entries.
- Kept, as agreed: 19,494 → 19,100 genuine return rows (some overlapped
  with removed junk/duplicates), and 234,507 rows with no customer_id
  (kept for shop-wide totals, excluded from the customer-level file).
- Produced two outputs matching the two different uses agreed: a
  shop-wide file (1,032,369 rows) and a customer-level file (797,862
  rows, customer_id always present).
- 8 unit tests written against hand-crafted edge cases (one per rule),
  all passing, rather than only spot-checked by eye on the full file.
- Full data dictionary with real counts: `docs/data_dictionary_online_retail.md`.

### Trustpilot

**Task:** inspect and clean the real Trustpilot reviews file.

- Rows processed: 123,181 raw → 123,175 after cleaning (99.995% kept) -
  this dataset was already very clean (0 missing values, 0 duplicates on
  first inspection).
- Removed: 1 phone-number-only review, 3 punctuation-only reviews, 2
  non-English reviews. A blanket minimum-length filter was deliberately
  rejected after checking it would have wrongly caught hundreds of short
  but genuine reviews.
- 6 unit tests written against hand-crafted edge cases, all passing.
- Full data dictionary with real counts: `docs/data_dictionary_trustpilot.md`.

### ASOS Digital Experiments

**Task:** inspect and clean the real ASOS experiment snapshots (this was
done in an earlier session, before the current 8-phase plan was formally
agreed - included here so all three datasets' cleaning work is tracked in
one place).

- Snapshots processed: 24,153 raw rows → 23,366 after dropping known
  data-quality issues.
- Data-quality issues found and handled: 779 rows (3.2%) with missing
  variance, 8 rows with zero sample count — both identified by profiling
  the actual file, not assumed.
- Full data dictionary with real counts: `docs/data_dictionary_asos.md`.

## Phase 6 — Test whether a fix actually works (ASOS re-analysis)

**Task:** re-analyse 78 real historical A/B tests with proper statistical
rigour (multiple-testing correction, effect stability over time), and
design + power one new hypothetical experiment.

- 23,366 cleaned snapshots → 381 test/metric/variant combinations
  analysed at their final snapshot.
- Result: 27.6% of tests significant at raw p<0.05 (raw), falling to 22.0%
  (within-experiment BH-FDR) and 17.8% (across-the-board BH-FDR) —
  i.e. **roughly a third of "significant" raw results would not survive
  correction for multiple testing**, a concrete, quantified illustration
  of why the correction matters.
- Of the tests that remained significant, ~20% (21/105) showed the
  effect's sign flipping after the first fifth of the test's duration —
  meaning the "final" call wasn't stable for a meaningful part of the run.
- All statistical functions unit-tested against `statsmodels` reference
  implementations (6/6 tests passing) rather than only spot-checked by eye.
- Runtime: full re-analysis (load, test, correct, plot, write report) on
  the full published dataset completes in well under 10 seconds on a
  personal laptop.

## Not yet done (tracked so scope stays honest)

- Statistical analysis on Online Retail II — not started (Phase 3).
- Churn/CLV modelling — not started (Phase 4).
- Trustpilot NLP module — not started (Phase 5).
- Bringing all findings together — not started (Phase 7).
- Live demo + AWS deployment — not started (Phase 8).
