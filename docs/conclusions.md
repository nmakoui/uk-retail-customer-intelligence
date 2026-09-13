# Bringing It Together: What This Project Actually Found

Three independent datasets, four modelling approaches, and two storage
paradigms all point at a small number of real, connected findings —
this document draws the lines between them rather than treating each
phase as a standalone exercise.

## 1. Returns are not the problem they look like — but the returns *experience* is

Phase 3 found returners spend ~4× more than non-returners (£1,883 vs
£469 median net spend, Mann-Whitney U, 95% CI £1,272–£1,549). Phase 4
then asked the follow-up question a naive analysis wouldn't: does that
same behaviour predict who *leaves*? It doesn't — SHAP on the churn
model shows `has_returned` contributing almost nothing (0.02) next to
`recency_days` (0.92). **Returns predict value; they barely predict
risk.** Two different questions, two different, defensible answers from
the same customer base.

But Phase 5's aspect-based sentiment adds a third angle the numbers
alone don't show: `returns_refunds` is the single **worst-rated**
aspect across all Trustpilot reviews (1.65★, against `customer_service`
at 3.33★). Read together: don't penalise or gatekeep returns — the
data says they're a marker of your most valuable customers, not a risk
signal — but the *process* customers go through when returning
something is a genuine, measurable source of dissatisfaction worth
fixing on its own terms, independent of any churn-risk business case.

## 2. What actually drives churn is boring, and that's useful

Recency of last purchase dominates the churn model by a wide margin,
not returns, not order value, not tenure. LightGBM's edge over a plain
logistic baseline is real but modest (ROC-AUC 0.812 vs 0.801) — a small
lift from a large increase in model complexity, and worth stating
plainly rather than oversold. The practical read: a simple
recency-based flag would already capture most of the signal a
much fancier model finds: complexity earned a small, real improvement
here, not a transformative one.

Phase 5's star-rating model showed the opposite pattern on a different
task: a plain TF-IDF + Logistic Regression model *beat* LightGBM
outright (0.521 vs 0.505 accuracy, every single class). Two models,
two datasets, two honest answers about when complexity helps — that
contrast is itself a finding, not just two unrelated results.

## 3. Rigour changes the answer, not just the confidence interval

Phase 6's ASOS re-analysis is the sharpest illustration of why the
statistical discipline in Phase 3 mattered: of 381 real test/metric
combinations, 27.6% look significant at face value, but only 17.8%
survive correction for testing multiple metrics at once. **A third of
"wins" a team might have shipped on don't hold up.** ~20% of the
results that did stay significant also showed their effect flip
direction after the first fifth of the test — a reminder that "stop
the test, ship the winner" can be premature even when the final number
looks clean.

## 4. The data has a natural shape, and the architecture should follow it

Phase 5.5 wasn't an added NoSQL requirement bolted onto unrelated data —
it's a direct consequence of what Phase 5 actually produced. Only 59%
of reviews have any aspect mention at all, and among those that do,
counts range from 1 to 20+. Modelling that in SQL means a real,
measured cost: reconstructing one densely-annotated review returns
**100 rows** for what is conceptually one record. The same review in
MongoDB is one document. Meanwhile the *other* half of this project —
customers, transactions, experiments — is exactly the fixed-shape,
relationally-clean data SQL is built for, with real joins, CTEs, and
window functions doing real work in Phases 3.5 and 4. Neither store
"wins" globally; each fits a different half of the same real dataset.

## 5. Intelligence only matters if something can act on it

Phase 8 turned Phases 3–6's findings into something usable rather than
a static report: the same trained churn, CLV, and SHAP artefacts serve
both a human clicking through Streamlit and an AI agent calling MCP
tools directly. The one live multi-turn Claude Desktop transcript
captured during this phase is arguably the most honest evidence in the
whole project of whether the system actually works end-to-end: asked
about a real customer, the agent correctly chained a churn lookup into
an explanation; asked to connect that customer's risk to unrelated
review data, it explicitly declined, because the dataset doesn't
support that link. That refusal is a feature, not a gap — it shows the
tool boundaries were built honestly rather than to *look* impressive.

## What this project cannot tell us

- **No causal claims.** Everything above is correlational (the churn
  and CLV models, the aspect-sentiment findings) or drawn from
  historical/simulated experiments (Phase 6) — nothing here establishes
  that fixing the returns process *would* reduce complaints, only that
  it's currently the most-complained-about aspect.
- **Reviews aren't linked to individual customers** in this dataset —
  the Trustpilot data and the Online Retail II transaction data are
  two separate real sources, joined at the *company* level in the
  architecture, not the *customer* level. The MCP transcript surfaced
  this limitation directly when asked to connect them.
- **No live business impact figures.** Every number above is a model
  metric or a measured property of the data — not a revenue or
  retention-rate projection, because nothing here would support one
  without a real intervention and a real holdout to measure it against.