## Phase 5 — Understand what customers say (complete)

**Task:** go beyond overall sentiment scoring — aspect-level sentiment,
topic modelling validated against ground truth, keyword extraction, and
a genuinely trained + explained rating-prediction model.

- Sentiment comparison on a stratified 9,999-review sample: VADER
  baseline (66.5% accuracy) vs the transformer
  `nlptown/bert-base-multilingual-uncased-sentiment` (78.9%).
- Aspect-based sentiment across 5 hand-defined aspects: returns_refunds
  worst (1.65★), delivery 2.89★, price and quality both 3.22★,
  customer_service best and most-mentioned (3.33★).
- BERTopic topic modelling: 42 topics, 45.6% unassigned outliers.
  Validated against Trustpilot's real category field - strong agreement
  for subject-specific topics (Utilities 84.7%, Legal 73.5%), confirmed
  generic "excellent service"-style topics are tone-clusters, not real
  topics.
- KeyBERT keyword extraction (MMR diversity, top 5 phrases/review):
  genuinely topic-relevant phrases per review (e.g. a birthday-cake
  complaint surfaced "dissapointed cake," "received carrot" - literal
  extractive spans, not always grammatical, which is an honest,
  expected property of the method rather than a defect).
- Explainable star-rating model: TF-IDF + Logistic Regression **beat**
  LightGBM on every single class (0.521 vs 0.505 accuracy, 0.485 vs
  0.474 macro F1) - the opposite of Phase 4's result, and a sensible
  one: sparse high-dimensional bag-of-words features favour a linear
  model. Explained with SHAP `LinearExplainer`. Confusion matrix shows
  the classic ordinal-middle problem (2★/3★ far harder than 1★/5★), but
  **69.3% of all wrong predictions were off by exactly one star** -
  evidence the model is directionally sensible even when not exactly
  right.
- **Outstanding:** the LoRA/PEFT fine-tune extension - lowest priority,
  not yet built, explicitly scoped as skippable if time is short.

## Phase 5.5 — NoSQL layer (complete)

**Task:** store the same real enrichment data in both PostgreSQL and
MongoDB, using genuine dual implementations to make an honest SQL vs
NoSQL comparison rather than a token add-on.

- MongoDB (via Docker locally, and via EFS-backed Fargate in
  production) holding 9,999 per-review documents - sentiment, a nested
  `aspects` array, `topic`, and `keywords` - built from Phase 5's
  separate output files.
- Real evidence for the "variable shape" claim: only 5,895 of 9,999
  reviews (59%) have any aspect mention at all; among those that do,
  counts range from 1 to 20+.
- Equivalent structure loaded into Postgres as three bridge tables:
  `review_sentiment` (9,999 rows, one per review), `review_aspects`
  (11,936 rows across 5,895 distinct reviews), `review_keywords`
  (49,964 rows).
- Found and fixed a real bug while building the Postgres loader:
  splitting keywords with pandas' `.str.split(" | ")` silently treated
  `|` as regex alternation rather than a literal separator, tripling
  the expected row count (136,131 instead of ~50,000) by splitting on
  every space. Fixed with a plain Python `.split()` via `.apply()`.
- Concrete, measured comparison in `docs/sql_vs_nosql.md`: reconstructing
  one real review (20 aspects × 5 keywords) via SQL joins returns
  **100 rows** for what is conceptually one record - a real, quantified
  demonstration of relational join fan-out, not a made-up example. The
  same review in MongoDB is one `find_one()` call.

## Phase 6 — Test whether a fix actually works (ASOS re-analysis)

*(unchanged from before - see above)*

## Phase 8 — Build a small live demo, then share it (complete)

**Task:** wrap the trained artefacts behind both a human-facing
dashboard and an agent-facing interface, deployed for real on AWS.

- Found and fixed a real gap before this phase could even start: Phase
  4's churn model was never persisted to disk at all (trained fresh
  in-memory every run); CLV saved its predictions but not the fitted
  model objects. Added `src/models/save_models_for_deployment.py` to
  properly serialise both - churn LightGBM refit on all 5,341
  customers, CLV's BG/NBD + Gamma-Gamma refit on 4,186 and saved as
  just their fitted parameters (the fitted objects themselves can't be
  pickled - `lifetimes` stores an internal lambda from the fitting
  step - worked around by rebuilding fresh fitter objects from the
  saved parameters, then manually re-attaching `.predict` since it's
  normally set up during `.fit()`).
- **FastAPI** (`api/main.py`), 4 endpoints: `/churn_risk`,
  `/customer_clv`, `/explain_prediction` (SHAP), and
  `/search_reviews_by_topic` (MongoDB-backed). Verified the SHAP
  explanation is mathematically consistent with the model's own
  prediction: base value + summed contributions, passed through a
  sigmoid, reproduces the exact churn probability the other endpoint
  returns.
- **Streamlit dashboard** (`app/streamlit_app.py`) - customer lookup
  showing churn risk, CLV, a SHAP bar chart, and topic-based review
  search.
- Dockerised all three services (Mongo, API, Streamlit) via
  `docker-compose.yml`. Found and fixed a real LightGBM-in-Docker gotcha
  along the way: the `python:3.12-slim` base image strips out
  `libgomp` (the OpenMP runtime), which LightGBM's compiled core
  silently needs regardless of `requirements.txt` - fixed with one
  `apt-get install libgomp1` line.
- **Deployed to AWS ECS Fargate** (cluster `retainscope-cluster`,
  eu-west-2): images pushed to ECR, EFS-backed persistent storage for
  Mongo, Cloud Map private DNS namespace (`retainscope.local`) so
  services address each other by stable name rather than a changing
  IP. Verified live end-to-end on public URLs, including the
  Mongo-backed topic search. **Scaled to 0 between demos** - Fargate
  bills continuously while running, unlike RDS's free tier.
- **MCP server** (`mcp_server/server.py`) exposing all 4 capabilities as
  MCP tools (`mcp>=2.0`, using the renamed `MCPServer` API). Tested and
  confirmed working via the MCP Inspector, then packaged as an
  installable `.mcpb` desktop extension (the current app version's
  actual path for local MCP servers, distinct from the classic
  `claude_desktop_config.json` JSON-editing approach) and **connected
  to a real Claude Desktop conversation**. A genuine multi-turn
  transcript is saved as evidence: Claude correctly chained
  `get_churn_risk` → `explain_prediction` in one turn and
  `get_customer_clv` + `search_reviews_by_topic` in a follow-up, while
  explicitly declining to claim a causal link between a customer's
  churn risk and unrelated delivery-complaint reviews that the data
  couldn't support.
- `AGENTS.md` written at the repo root, covering both the MCP tools'
  purpose and the real environment-setup gotchas hit throughout this
  build (Windows launcher/PATH issues, CRLF line endings, case-sensitive
  `scripts/` folder).

## Not yet done (tracked so scope stays honest)

- The LoRA/PEFT fine-tune - not started (remaining Phase 5 extension,
  explicitly lowest priority).
- Bringing all findings together into one conclusion - not started
  (Phase 7).