# UK Retail Customer Intelligence & Experimentation Platform

A portfolio project simulating a UK retail analytics consultancy running
three parallel client engagements. Full rationale and phase-by-phase plan:
see `docs/project.md`.

**Status: Phases 1-4 and 6 (data cleaning, statistical analysis, AWS RDS +
SQL data layer, churn/CLV modelling with SHAP, and ASOS experimentation
re-analysis) are done. Phase 5 (NLP) is in progress — sentiment, aspect-
based sentiment, and topic modelling are built; keyword extraction, the
rating-prediction model, and a small fine-tune are still to come. Phases
5.5 (NoSQL), 7 (bringing findings together), and 8 (deployment, including
an MCP agent interface) are not started yet — see `docs/impact_log.md`
for progress.**

## What's actually implemented right now

`src/experimentation/` — a from-scratch re-analysis pipeline for the
**ASOS Digital Experiments Dataset** (Liu et al., 2021: 78 real A/B tests
run by ASOS.com, a UK fashion retailer), validated unit-test-by-unit-test
against `statsmodels` reference implementations. It:

1. Loads the raw aggregated snapshots and classifies each of the 4
   organisational metrics as binary (proportion) or continuous, based on
   actually profiling the data (metric 1's variance exactly matches
   `p(1-p)`; metrics 2-4 don't) — not assumed from the paper alone.
2. Handles two real data-quality issues found in the published file:
   ~3.2% of continuous-metric rows have a missing variance, and 8 rows
   have a zero sample count in one arm. Both are dropped and logged
   rather than silently imputed.
3. Re-computes the concluding effect, standard error, z-statistic,
   p-value and 95% CI for every (experiment, variant, metric) combination
   at its final snapshot — validated against `statsmodels.proportions_ztest`
   for the binary case.
4. Applies Benjamini-Hochberg FDR correction two ways (within each
   experiment's own 4 metrics, and across the whole 381-test collection)
   and reports how the "% significant" figure changes under each.
5. Checks effect **stability over time** for tests with ≥5 snapshots,
   restricted to tests that were actually significant at the end (checking
   near-null effects for "sign flips" would just be measuring noise).
6. Designs and powers a **new, hypothetical** retention-email experiment
   (Phase 6b), then simulates one run of it under the design assumptions —
   clearly labelled as synthetic, never presented as observed.

### Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.experimentation.run_reanalysis
pytest tests/ -v
```

Outputs land in `reports/` (`asos_reanalysis_summary.csv`,
`asos_reanalysis_report.md`) and `reports/figures/`.

### Headline results on the real data (see `reports/asos_reanalysis_report.md` for the live numbers)

- 27.6% of the 381 test/metric/variant combinations are significant at raw
  p < 0.05 — close to the ~25% figure often cited for this exact dataset,
  which is a nice sanity check that the re-implementation is correct.
- That drops to 22.0% (within-experiment FDR) and 17.8% (across-the-board
  FDR) after correcting for the fact most experiments test 4 metrics at
  once.
- Among the significant results, ~20% show the effect's sign flipping
  after the first fifth of the observation window — i.e. the final
  "winning" call wasn't stable throughout the test. Two of the plotted
  examples show a classic decaying novelty effect.

## Statistics on Online Retail II (Phase 3)

Built a per-customer RFM (Recency, Frequency, Monetary) table for ~5,940
customers, then tested two specific, pre-registered questions properly —
checking skewness first to pick the right test, rather than defaulting to
a t-test.

- **Returners spend ~4× more overall** (median £1,883 vs £469 net spend)
  than customers who've never returned anything — Mann-Whitney U (used
  because spend is heavily right-skewed), 95% bootstrap CI on the gap:
  £1,272–£1,549. Directly overturns the assumption that returns are a
  warning sign.
- **No meaningful difference in order value, 2010 vs 2011** (p = 0.38) —
  an honest null result, reported as such rather than omitted.
- Deliberately did **not** apply multiple-testing correction here (only
  two pre-registered questions) — contrast against Phase 6's 381 tests,
  where it was genuinely warranted.

## SQL & Cloud Database (Phase 3.5)

A real AWS RDS PostgreSQL database (`retainscope-db`), not local CSVs —
built and queried by hand, not generated.

- Free-tier `db.t4g.micro`, hosted in **eu-west-2 (London)** — a
  deliberate region choice given the UK focus of all three datasets, not
  a default.
- A 7-table dimension/fact schema across all three datasets: `products`,
  `customers`, `transactions` (Online Retail II); `companies`, `reviews`
  (Trustpilot); `experiments`, `experiment_results` (ASOS).
- **~1.18M rows loaded** (1,032,369 transactions + 123,175 reviews +
  23,366 experiment results), verified row-for-row against Phase 2's
  documented cleaning counts.
- Found and fixed a real gap during this phase: the ASOS cleaned file had
  never actually been exported from Phase 2 — re-ran and re-saved that
  cleaning step, confirming it reproduced the exact same 23,366-row count.
- **4 SQL queries** (`sql/phase3_5_queries.sql`) demonstrating CTEs,
  joins, and two window-function patterns (`RANK() OVER (PARTITION BY
  ...)`, running `SUM() OVER (...)`) — including independently
  reproducing the Phase 3 returners finding to the penny, using
  `PERCENTILE_CONT` for the median (no built-in `MEDIAN()` in standard SQL).
- Secured with IP-restricted security group rules, not left open to the
  internet.

### Run it

```bash
# requires a .env file with DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
python scripts/load_online_retail.py
python scripts/load_trustpilot.py
python scripts/clean_asos.py && python scripts/load_asos.py
```
Then run `sql/phase3_5_queries.sql` against the database in any
PostgreSQL client (developed against DBeaver).

## Churn & CLV Modelling + SHAP (Phase 4)

Two models, two different real questions, both genuinely explained rather
than just scored.

- **Churn**, defined via a 3-month calibration/holdout split (cutoff
  2011-09-09): a customer is labelled churned if they made no purchase in
  the dataset's final 3 months, given their history beforehand.
- Compared a **Logistic Regression baseline against LightGBM** —
  LightGBM modestly outperforms (**ROC-AUC 0.812 vs 0.801**), a small,
  believable gap given both see the same 6 features.
- **SHAP (TreeExplainer)** on the churn model: `recency_days` dominates
  everything else (mean |SHAP| 0.92 vs next-highest 0.38).
  `has_returned` contributes almost nothing (0.02) — **returns predict a
  customer's value (Phase 3), but barely at all whether they'll leave.**
  Two different questions, two different, honest answers.
- **CLV modelled with BG/NBD + Gamma-Gamma** (the `lifetimes` library) —
  the standard statistical approach for non-contractual purchase
  settings, rather than a simple regression.
- Genuinely validated BG/NBD against a held-out window before trusting
  it: correlation between predicted and actual repeat purchases of
  **0.807** (customer-level ranking is reliable), but total predicted
  volume undershoots actual by **~23%** — most likely because BG/NBD
  assumes a constant purchase rate and can't capture the pre-Christmas
  seasonal surge visible in the holdout window. Also fit Pareto/NBD for
  comparison (0.808 correlation, same undershoot) — ruled out the "when
  can a customer die" assumption as the cause, since changing it made no
  difference.
- Found and fixed a real data-entry error while building this: one
  customer's single 80,995-unit, £168k order (cancelled 12 minutes later)
  was inflating their predicted CLV to a false #1 ranking. Added a
  same-day-full-reversal detection step that excludes genuine matched
  pairs, without touching real partial returns.
- **SHAP (KernelExplainer**, since BG/NBD + Gamma-Gamma aren't tree
  models**)** on the final 3-month CLV prediction: `monetary_value`,
  tenure (`T`), `frequency`, and `recency` (here meaning time between
  *first and last* purchase — a different definition than the churn
  model's "days since last purchase") all contribute meaningfully, with
  no single dominant feature the way churn had.

### Run it

```bash
# requires the Phase 3.5 database to be populated first —
# these scripts pull directly from PostgreSQL, not local CSVs
python src/models/train_churn_model.py
python src/models/explain_churn_model.py
python src/models/train_clv_model.py
python src/models/explain_clv_model.py
```

Figures land in `reports/figures/` (`phase4_shap_*.png`,
`phase4_clv_shap_*.png`).

## Customer Voice & NLP (Phase 5, in progress)

Sentiment, aspect-level sentiment, and topic modelling on a stratified
sample of Trustpilot reviews — going beyond a single overall polarity
score.

- Stratified sample of 9,999 reviews from the cleaned 123,175-review set,
  preserving the real star-rating distribution.
- **Sentiment: transformer beats lexicon baseline** — VADER 66.5%
  accuracy vs. `nlptown/bert-base-multilingual-uncased-sentiment` 78.9%.
  Unlike Phase 4's small baseline-vs-LightGBM gap, here the added
  complexity clearly earns its keep.
- **Aspect-based sentiment** across 5 hand-defined aspects
  (keyword-matched, transformer-scored per sentence): `returns_refunds`
  worst at 1.65★, `delivery` 2.89★, `price` and `quality` both 3.22★,
  `customer_service` best and most-mentioned at 3.33★.
- **BERTopic topic modelling**: 42 topics, with 45.6% of reviews left as
  unassigned outliers.
- Validated the topics against Trustpilot's own `category` field rather
  than taking topic quality on faith — strong agreement for
  subject-specific topics (Utilities 84.7%, Legal 73.5%), and confirmed
  that broad "excellent service"-style topics are tone-clusters rather
  than real subject topics; genuinely cross-cutting operational language
  (delivery/ordering) does span categories even where it is a real topic.
- **Still to build:** keyword extraction (KeyBERT), an explainable model
  predicting star rating from review text + SHAP, and a small LoRA/PEFT
  fine-tune of DistilBERT as one more row in the sentiment comparison
  (see `docs/project.md`).

### Run it

```bash
python scripts/sample_trustpilot_reviews.py
python src/nlp/sentiment_comparison.py
python src/nlp/aspect_sentiment.py
python src/nlp/topic_modeling.py
python src/nlp/topic_category_validation.py
```

Outputs land in `data/processed/` (`trustpilot_nlp_sample.csv`,
`trustpilot_sentiment_comparison.csv`, `trustpilot_aspect_sentiment.csv`,
`trustpilot_topics_assigned.csv`, `trustpilot_topics_summary.csv`,
`trustpilot_topic_category_validation.csv`) and the trained topic model
in `models/bertopic_model`.

## What's next
- Finish Phase 5: keyword extraction (KeyBERT), star-rating explainable
  model, LoRA/PEFT fine-tune
- NoSQL layer — MongoDB alongside PostgreSQL, plus a SQL vs NoSQL note
  (Phase 5.5)
- Bringing all findings together into one conclusion (Phase 7)
- Live demo + AWS deployment, including an MCP agent interface and
  `AGENTS.md` (Phase 8)

See `docs/project.md` for the full plan and `docs/impact_log.md` for
what's been measured so far.