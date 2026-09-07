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

## Phase 3 — Understand customers with statistics

**Task:** test specific hypotheses about customer behaviour on Online
Retail II, checking assumptions before choosing a test rather than
defaulting to a t-test.

- Returners spend ~4× more than non-returners: £1,883 vs £469 median net
  spend (Mann-Whitney U — chosen after checking the spend distribution is
  skewed, not normal), 95% bootstrap CI on the gap £1,272–£1,549. A large,
  statistically robust difference that directly overturns the assumption
  that returns are simply a bad sign.
- No real order-value difference between 2010 and 2011 (p = 0.38) — an
  honest null result, reported as such rather than dropped.

## Phase 3.5 — SQL & Cloud Database

**Task:** stand up a real cloud SQL layer (not local CSVs) and reproduce
a prior finding independently in SQL, to prove the pipeline and the
finding both hold up outside pandas.

- Real AWS RDS PostgreSQL instance (`retainscope-db`, free-tier
  db.t4g.micro, eu-west-2/London), connected via DBeaver.
- 7-table dimension/fact schema loaded: `products`, `customers`,
  `transactions` (Online Retail II) · `companies`, `reviews` (Trustpilot)
  · `experiments`, `experiment_results` (ASOS). 1,032,369 transactions ·
  123,175 reviews · 23,366 experiment_results loaded and verified.
- Found and fixed a real gap along the way: the ASOS cleaned file had
  never actually been exported from Phase 2 — re-ran and re-saved it.
- 4 SQL queries (`sql/phase3_5_queries.sql`) covering CTEs, dimension/fact
  joins, `RANK() OVER (PARTITION BY ...)`, and running `SUM() OVER` —
  independently reproduced the Phase 3 returners finding to the penny
  (£469.02 vs £1,883.07 median spend).

## Phase 4 — Predict who's leaving, and explain why

**Task:** build a churn model and a CLV model on real transaction data,
explain both with SHAP, and catch any data-quality issues that would
distort the numbers before trusting them.

- Churn: 3-month holdout (cutoff 2011-09-09), near-balanced classes
  (43.6% active / 56.4% churned). Logistic regression baseline (ROC-AUC
  0.801) vs LightGBM (ROC-AUC 0.812). SHAP TreeExplainer shows
  `recency_days` dominates, while `has_returned` barely matters (0.02) —
  a direct, explainable contrast with Phase 3's finding that returns
  predict *value*, not churn *risk*.
- CLV: BG/NBD + Gamma-Gamma, validated against a holdout (correlation
  0.807), with a ~23% volume undershoot attributed to pre-Christmas
  seasonality — confirmed rather than assumed, by also testing Pareto/NBD
  and getting the same undershoot. SHAP KernelExplainer applied.
- Found and fixed a real data-entry error: a single customer's erroneous
  80,995-unit, £168k order (cancelled 12 minutes later) was distorting
  their CLV estimate. Added same-day full-reversal detection, which
  excluded 592 invoices without touching legitimate partial returns.

## Phase 5 — Understand what customers say (in progress)

**Task:** go beyond overall sentiment scoring — aspect-level sentiment,
topic modelling validated against ground truth, and an honest comparison
of approaches rather than picking one and moving on.

- Sentiment comparison on a stratified 9,999-review sample: VADER
  baseline (66.5% accuracy) vs the transformer
  `nlptown/bert-base-multilingual-uncased-sentiment` (78.9%).
- Aspect-based sentiment across 5 hand-defined aspects: returns_refunds
  worst (1.65★), delivery 2.89★, price and quality both 3.22★,
  customer_service best and most-mentioned (3.33★).
- BERTopic topic modelling: 42 topics, 45.6% unassigned outliers.
  Validated against Trustpilot's real category field rather than taken
  on faith — strong agreement for subject-specific topics (Utilities
  84.7%, Legal 73.5%), and confirmed that the generic "excellent
  service"-style topics are tone-clusters, not real topics.
- **Still to do:** keyword extraction (KeyBERT), an explainable model
  predicting star rating from review text (+ SHAP), and a small
  LoRA/PEFT fine-tune of DistilBERT as one more row in the sentiment
  comparison (see `docs/project.md`).

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

- Keyword extraction, star-rating explainable model, and the LoRA/PEFT
  fine-tune — not started (remaining Phase 5 work).
- NoSQL layer (MongoDB + SQL vs NoSQL note) — not started (Phase 5.5).
- Bringing all findings together — not started (Phase 7).
- Live demo + AWS deployment, including the MCP agent interface and
  `AGENTS.md` — not started (Phase 8).