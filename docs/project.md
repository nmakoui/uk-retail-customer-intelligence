# UK Retail Customer Intelligence & Experimentation Platform
### RetainScope — MSc Data Science portfolio project

---

## 0. The Core Data Science Question

Every strong DS portfolio project needs one sentence a recruiter can repeat back to you. Yours is:

> **"Which UK retail customers are likely to churn and what is their predicted future value — and, independently, which product/service attributes and customer-voice themes actually drive satisfaction and dissatisfaction across UK retail categories — so that retention spend and messaging can be prioritised, and can we validate a proposed retention action with a properly powered experiment before recommending it?"**

This forces you to demonstrate, in order: **statistics → supervised ML → NLP → explainability → experimentation → business translation.**

Three extensions sit on top of that same question rather than beside it: the customer-voice output needs a storage layer that actually fits its shape (NoSQL), the trained models need to be usable by more than a human clicking a dashboard (an agent interface), and the sentiment comparison already underway deserves one more honest data point (a small fine-tune). None of these are a fourth project — each is "I extended X to also do Y," which is a stronger interview answer than a standalone gap-filling exercise.

---

## 1. What this project simulates

You are a **Data Scientist inside a UK retail analytics consultancy** serving e-commerce clients, running three engagements in parallel:

| Client engagement | Dataset | Core skill demonstrated |
|---|---|---|
| **A. Retention & Value** | Online Retail II | Statistics, feature engineering, churn/CLV ML, explainability |
| **B. Customer Voice** | Trustpilot Reviews 123k | Serious NLP, aspect-based sentiment, explainable text models |
| **C. Experimentation** | ASOS Digital Experiments Dataset | Power analysis, hypothesis testing, causal inference, experiment design |

All three roll up into one deployed product with **two front doors**: a human-facing Streamlit view and an agent-facing MCP server, both backed by the same trained artefacts.

---

## 2. Datasets — all real, all free, all UK-sourced

*(Unchanged from the original plan — Online Retail II, Trustpilot Reviews 123k, ASOS Digital Experiments. See `docs/data_dictionary_*.md` for the real, as-cleaned counts and caveats for each.)*

---

## 3. Updated architecture
RAW DATA (3 sources, UK)
│
▼
Python ETL — extraction, validation, cleaning, transformation
│
▼
┌────────────────────────────┐
│ PostgreSQL (AWS RDS) │ dim/fact model — customers, products,
│ │ transactions, companies, reviews,
│ │ experiments, experiment_results
└──────────────┬─────────────┘
│
▼
ANALYTICS LAYER
SQL analytics │ Stats │ ML + SHAP │ NLP
│
├──────────────────────────────┐
▼ ▼
┌───────────────────────┐ ┌──────────────────────────┐
│ MongoDB │ │ Same NLP output written │
│ one document per review│◄────►│ back to Postgres as a │
│ nested aspect/topic │ │ bridge table / JSON col │
│ fields — variable-shaped│ │ — same real data, both │
│ by nature │ │ stores, documented │
└───────────────────────┘ └──────────────────────────┘
│
▼
Trained artefacts (churn, CLV, sentiment, SHAP explainers)
│
┌───────┴────────┐
▼ ▼
Streamlit MCP server
(human-facing) (agent-facing, via mcp>=2.0)
Dockerised FastAPI behind both, on AWS

---

## 4. Phase-by-phase plan

Status (done/in progress/not started) lives in `PROJECT_PHASES_STATUS.md`, kept current there — this section is scope, not status.

- **Phase 1 — Workspace setup**
- **Phase 2 — Data cleaning** (all three datasets)
- **Phase 3 — Statistics** (hypothesis tests, effect sizes, bootstrap CIs, justified use of FDR correction)
- **Phase 3.5 — SQL & Cloud Database** (AWS RDS PostgreSQL, hand-written joins/window functions/CTEs)
- **Phase 4 — Churn/CLV modelling + SHAP**
- **Phase 5 — Customer Voice & NLP** — sentiment (baseline vs. transformer), aspect-based sentiment, BERTopic topic modelling, keyword extraction (KeyBERT), explainable rating-prediction model.
  - **Extension — fine-tuning (Addition 3):** add one more row to the existing sentiment/aspect comparison — a small LoRA/PEFT fine-tune of an open-source model (DistilBERT-sized) on your own labelled review data, for the same classification task. Report accuracy alongside the lexicon and off-the-shelf transformer numbers, honestly scaled to the size of the labelled set. This is the smallest of the three additions — do it last, and it's the one to skip first if time is tight.
- **Phase 5.5 — NoSQL layer (Addition 1, essential)**
  Take the enriched output of Phase 5 — per-review sentiment, aspect scores, topics, keywords — and store it in **MongoDB** as one document per review, with nested aspect/topic fields. This is a genuine NoSQL use case, not a contrived one: different reviews surface different aspects/topics, which is awkward to force into rigid SQL columns.
  - Write the equivalent structure into the existing PostgreSQL schema (a bridge table or JSON column) so the same real data exists in both stores.
  - Write a short **"SQL vs NoSQL" note** (extends the existing "honest documentation of what I found and fixed" habit) using your own two implementations as evidence: relational wins for the fact/dimension churn/CLV joins with window functions already built in Phase 3.5/4; document store wins for the sentiment/topic annotations that vary review-to-review.
- **Phase 6 — ASOS experimentation re-analysis** (78 real A/B tests, FDR correction, effect-stability check, new powered experiment)
- **Phase 7 — Bring findings together**
- **Phase 8 — Deployment** — Dockerised FastAPI + Streamlit, deployed on AWS.
  - **Extension — MCP server + AGENTS.md (Addition 2, desirable):** wrap the trained artefacts as MCP tools alongside (or instead of) REST endpoints — `get_churn_risk(customer_id)`, `get_customer_clv(customer_id)`, `explain_prediction(customer_id)` (backed by the SHAP explainers), `search_reviews_by_topic(topic)` (backed by the new MongoDB store). Build with the official Python SDK (`mcp[cli]`, check `mcp>=2.0` — the SDK had a major rework), test with `npx @modelcontextprotocol/inspector` before wiring it up, then connect it to Claude and record a real multi-turn transcript (e.g. "which customers are high churn risk and why" triggering `get_churn_risk` then `explain_prediction` in sequence) — that transcript is the interview evidence. Write `AGENTS.md` documenting what the agent can do, after looking at a couple of real repo examples so it reads like the actual convention. Streamlit stays the human-facing view; MCP is the agent-facing one — having both in the same deployment phase is a stronger story than either alone.

---

## 5. Technology stack

| Category | Tools |
|---|---|
| Core | Python, Pandas, NumPy, SQL |
| Statistics | SciPy, statsmodels |
| ML | scikit-learn, LightGBM, `lifetimes` (CLV) |
| Explainability | SHAP |
| NLP | Hugging Face Transformers, BERTopic, KeyBERT, VADER |
| Fine-tuning | Hugging Face `transformers` Trainer, PEFT (LoRA) |
| Experimentation | statsmodels power analysis, custom power/FDR scripts |
| Data engineering | PostgreSQL (AWS RDS), SQLAlchemy, **MongoDB, PyMongo** |
| Agent interface | **`mcp` (Python SDK, ≥2.0), MCP Inspector** |
| Deployment/Cloud | FastAPI, Streamlit, Docker, AWS |
| Dev practice | Git, GitHub, pytest, `.env` for secrets (never committed) |

---

## 6. The 10 goals this project must keep serving

| Goal | Where it's covered |
|---|---|
| 1. Attract UK recruiters / help me get hired | Real UK datasets, a live demo, honest documentation |
| 2. Proper statistical analysis | Phase 3 |
| 3. Experimentation + serious NLP | Phase 6, Phase 5 |
| 4. Explainability | Phase 4, Phase 5 |
| 5. Deployment | Phase 8 |
| 6. Cloud (AWS) | Phase 3.5, Phase 8 |
| 7. SQL | Phase 3.5 |
| 8. NoSQL / polyglot persistence | Phase 5.5 |
| 9. Agentic / MCP interface | Phase 8 extension |
| 10. Fine-tuning | Phase 5 extension |

---

## 7. Traps to avoid

- Don't force the three datasets into one artificial join — present them as three linked engagements.
- Don't skip assumption checks or multiple-comparison correction before hypothesis tests.
- Don't present the simulated experiment as real data anywhere, including on LinkedIn.
- Don't claim revenue/business impact the data can't support.
- Don't let MongoDB become a second, undocumented source of truth — the SQL vs NoSQL note is what justifies having both.
- Don't demo the MCP server as a gimmick — the recorded multi-turn transcript is the actual evidence, keep it.
- Don't oversell the fine-tune — a small LoRA run on a small labelled set is one more honest row in the comparison table, not a headline result.