# UK Retail Customer Intelligence & Experimentation Platform

A portfolio project simulating a UK retail analytics consultancy running
three parallel client engagements. Full rationale and phase-by-phase plan:
see `docs/project.md`.

**Status: Phases 1-6 and 8 are done. Only Phase 7 (bringing findings
together) and an optional LoRA/PEFT fine-tune remain — see
`docs/impact_log.md` for full detail on everything built.**

## What's actually implemented right now

`src/experimentation/` — a from-scratch re-analysis pipeline for the
**ASOS Digital Experiments Dataset** (78 real A/B tests run by
ASOS.com), validated against `statsmodels` reference implementations.
27.6% of 381 test/metric/variant combinations significant at raw
p<0.05, dropping to 17.8% after FDR correction across the board;
~20% of significant results show their effect's sign flipping after
the first fifth of the run.

### Run it
```bash
python -m src.experimentation.run_reanalysis
pytest tests/ -v
```

## Statistics on Online Retail II (Phase 3)
Returners spend ~4× more overall (£1,883 vs £469 median net spend,
Mann-Whitney U, 95% bootstrap CI £1,272–£1,549). No real order-value
difference 2010 vs 2011 (p = 0.38) — an honest null result.

## SQL & Cloud Database (Phase 3.5)
AWS RDS PostgreSQL (`retainscope-db`, eu-west-2). 7-table dim/fact
schema, ~1.18M rows loaded across all three datasets. 4 SQL queries
(`sql/phase3_5_queries.sql`) independently reproduce the returners
finding to the penny.

### Run it
```bash
python scripts/load_online_retail.py
python scripts/load_trustpilot.py
python scripts/clean_asos.py && python scripts/load_asos.py
```

## Churn & CLV Modelling + SHAP (Phase 4)
Churn: LightGBM (ROC-AUC 0.812) vs logistic baseline (0.801). SHAP shows
`recency_days` dominates; `has_returned` barely matters — returns
predict value, not churn risk. CLV: BG/NBD + Gamma-Gamma, 0.807
correlation on holdout. Caught and fixed a real £168k erroneous-order
data-entry error.

### Run it
```bash
python src/models/train_churn_model.py
python src/models/explain_churn_model.py
python src/models/train_clv_model.py
python src/models/explain_clv_model.py
```

## Customer Voice & NLP (Phase 5, complete)
- Sentiment: VADER (66.5%) vs transformer `nlptown/bert-base-multilingual-uncased-sentiment` (78.9%).
- Aspect-based sentiment (5 aspects): `returns_refunds` worst (1.65★), `customer_service` best (3.33★).
- BERTopic: 42 topics, 45.6% outliers, validated against Trustpilot's real category field.
- KeyBERT keyword extraction (MMR diversity, top 5 phrases/review).
- Star-rating model: **Logistic Regression beat LightGBM here** (0.521 vs 0.505 accuracy) — the opposite of Phase 4's result, sensible given sparse TF-IDF features favour linear models. SHAP `LinearExplainer`. 69.3% of wrong predictions off by exactly one star.
- **Still to build:** a small LoRA/PEFT fine-tune of DistilBERT as one more row in the sentiment comparison — lowest priority, explicitly skippable.

### Run it
```bash
python scripts/sample_trustpilot_reviews.py
python src/nlp/sentiment_comparison.py
python src/nlp/aspect_sentiment.py
python src/nlp/topic_modeling.py
python src/nlp/topic_category_validation.py
python src/nlp/keyword_extraction.py
python src/nlp/star_rating_model.py
```

## NoSQL Layer (Phase 5.5, complete)
The same enriched review data — sentiment, aspects, topic, keywords —
lives in both MongoDB (one document per review, nested `aspects`
array) and PostgreSQL (three bridge tables: `review_sentiment`,
`review_aspects`, `review_keywords`). Real evidence for the "variable
shape" story: only 59% of reviews have any aspect mention at all,
ranging from 1 to 20+ per review. Concrete comparison in
`docs/sql_vs_nosql.md`: reconstructing one real review via SQL joins
returns **100 rows** for what's conceptually one record; the same
review in MongoDB is one `find_one()` call.

### Run it
```bash
docker run -d --name retainscope-mongo -p 27017:27017 -v retainscope_mongo_data:/data/db mongo:7
python scripts/load_reviews_to_mongo.py
# run sql/phase5_5_schema.sql in DBeaver first, then:
python scripts/load_review_enrichment_to_postgres.py
```

## Deployment (Phase 8, complete)
- **FastAPI** (`api/main.py`): `/churn_risk`, `/customer_clv`,
  `/explain_prediction` (SHAP), `/search_reviews_by_topic` (MongoDB).
- **Streamlit** (`app/streamlit_app.py`): customer lookup dashboard
  with churn risk, CLV, a SHAP bar chart, and topic-based review search.
- **Dockerised** all three services via `docker-compose.yml`.
- **Deployed live on AWS ECS Fargate** (`retainscope-cluster`,
  eu-west-2) — ECR images, EFS-backed Mongo storage, Cloud Map private
  DNS (`retainscope.local`) so services address each other by stable
  name. **Scaled to 0 between demos** — Fargate bills continuously
  while running.
- **MCP server** (`mcp_server/server.py`) exposing all 4 capabilities
  as MCP tools, packaged as a `.mcpb` desktop extension, connected to a
  real Claude Desktop conversation — transcript saved as evidence.
- See `AGENTS.md` for environment gotchas and the full MCP tool list.

### Run it locally
```bash
docker compose up --build
# API:       http://127.0.0.1:8000/docs
# Streamlit: http://127.0.0.1:8501
```

### Redeploy to AWS (after scaling to 0)
```bash
aws ecs update-service --cluster retainscope-cluster --service mongo-service --desired-count 1 --region eu-west-2
aws ecs update-service --cluster retainscope-cluster --service api-service --desired-count 1 --region eu-west-2
aws ecs update-service --cluster retainscope-cluster --service streamlit-service --desired-count 1 --region eu-west-2
```

## What's next
- Optional: LoRA/PEFT fine-tune (Phase 5 extension, lowest priority)

See `docs/conclusions.md` for the full synthesis, `docs/project.md` for
the plan, `docs/impact_log.md` for everything measured, and
`AGENTS.md` for environment setup and the MCP tool reference.