# UK Retail Customer Intelligence & Experimentation Platform
### A redesign of the Digikala case study for the UK market — MSc Data Science portfolio project

---

## 0. The Core Data Science Question

Every strong DS portfolio project needs one sentence a recruiter can repeat back to you. Yours is:

> **"Which UK retail customers are likely to churn and what is their predicted future value — and, independently, which product/service attributes and customer-voice themes actually drive satisfaction and dissatisfaction across UK retail categories — so that retention spend and messaging can be prioritised, and can we validate a proposed retention action with a properly powered experiment before recommending it?"**

This single question forces you to demonstrate, in order: **statistics → supervised ML → NLP → explainability → experimentation → business translation.** That range (not any single technique) is what makes a portfolio project stand out to a UK hiring manager, because it maps directly onto the actual DS workflow at a retail/marketing analytics employer rather than a Kaggle leaderboard exercise.

---

## 1. What this project simulates

You are a **Data Scientist inside a UK retail analytics consultancy** (this replaces the Tehran marketing-agency framing) serving e-commerce clients. The consultancy has three engagements running in parallel, each a self-contained but connected module:

| Client engagement | Dataset | Core skill demonstrated |
|---|---|---|
| **A. Retention & Value** | Online Retail II | Statistics, feature engineering, churn/CLV ML, explainability |
| **B. Customer Voice** | Trustpilot Reviews 123k | Serious NLP, aspect-based sentiment, explainable text models |
| **C. Experimentation** | ASOS Digital Experiments Dataset | Power analysis, hypothesis testing, causal inference, experiment design |

All three roll up into one deployed mini-product and one Power BI story. This structure is *stronger* than trying to force one artificial product↔review join — it mirrors how a consultancy actually works across clients, and it lets you show breadth without faking a relationship in the data that isn't really there.

---

## 2. Datasets — all real, all free, all UK-sourced

### A. Online Retail II (behavioural / transactional layer)
- Real transactions (Dec 2009–Dec 2011) from a UK-registered, non-store online retailer selling giftware, with wholesaler customers included.
- Fields: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country.
- Source: UCI ML Repository (ID 502) or Kaggle mirror `mashlyn/online-retail-ii-uci`.
- **Caveat to state honestly in your README:** this is a well-known dataset. Your differentiation comes from what you *do* with it (proper time-based train/test split, leakage checks, calibrated churn probabilities, CLV under uncertainty), not from the dataset novelty.

### B. Trustpilot Reviews 123k (customer voice / NLP layer)
- 123,181 English-language UK Trustpilot reviews, 1,680 companies, 22 categories, collected Dec 2024–Jan 2025.
- Fields include review title, body, star rating, company, category.
- Source: Kaggle `jerassy/trustpilot-reviews-123k` or the Hugging Face mirror. MIT-licensed.
- **Optional extension for extra credit:** scrape a small, fresh sample (a few hundred reviews) from 2–3 specific UK retailers' Trustpilot pages yourself, respecting robots.txt/rate limits, to show you can also build a lightweight ethical scraper — but the 123k set alone is enough; don't let scraping become scope creep.

### C. ASOS Digital Experiments Dataset (experimentation layer)
- 78 real, anonymised A/B tests from a business unit within ASOS.com (UK fashion e-commerce), 2019–2020, with daily/12-hourly aggregated snapshots across 4 organisational metrics.
- Group-level aggregates only (counts, means, variances per arm) — no user-level data, which is realistic: most companies won't hand you raw experiment logs either, so working from summary statistics is itself a transferable skill.
- Source: OSF `https://osf.io/64jsb/`, Kaggle mirror `marinazmieva/asos-digital-experiments-dataset`, companion analysis code at GitHub `liuchbryan/oce-dataset`.
- This dataset has been used and praised publicly by well-known names in the experimentation field (e.g. Ron Kohavi), so referencing it correctly signals you know the space, not just that you ran `scipy.stats.ttest_ind` once.

---

## 3. Updated architecture

```
RAW DATA (3 sources, UK)
        │
        ▼
┌─────────────────────┐
│   Python ETL         │  extraction, validation, cleaning, transformation
└─────────┬────────────┘
          ▼
┌─────────────────────┐
│  PostgreSQL           │  local for dev; optionally AWS RDS free tier for the
│  (dim/fact model)      │  "production" version — see Phase 10
└─────────┬────────────┘
          ▼
┌───────────────────────────────────────────────────────────┐
│                     ANALYTICS LAYER                          │
│  SQL analytics │ Statistical testing │ NLP │ ML + SHAP        │
└─────────┬─────────────────────────────────────┬─────────────┘
          ▼                                     ▼
   Experimentation module                Power BI dashboards
   (power analysis, re-analysis                 │
    of ASOS tests, new test design)              ▼
          │                              Business recommendations
          ▼                              (with honest impact log)
   Small deployed app (FastAPI/Streamlit, Dockerised, on AWS)
```

---

## 4. Phase-by-phase plan

### Phase 0 — Setup
Same discipline as the original plan (Git repo, folder structure, venv, `requirements.txt`, `.gitignore`, README, coding conventions), plus:
- `docker-compose.yml` for local Postgres from day one, so containerisation isn't bolted on later.
- A `Makefile` or `justfile` with `make setup`, `make etl`, `make test` — small but it signals engineering maturity to a recruiter skimming your repo.

### Phase 1 — Data understanding & quality
Keep the original's rigour (missingness, duplicates, cardinality, referential integrity, outliers) applied to **all three datasets independently**. Add:
- A short **data limitations section** per dataset (e.g. "Online Retail II has no cancellations for ~9% of invoices flagged with 'C' — decide and justify how you handle these before any CLV work").
- For the ASOS dataset specifically: document that it's aggregated, not user-level, and what that does and doesn't let you compute.

### Phase 2 — Python ETL
Same modular structure as the original (`extract.py`, `transform_*.py`, `validate.py`, `load.py`, `pipeline.py`), with logging, error handling, config-driven runs. Track the same engineering metrics (rows processed, runtime, invalid/duplicate counts) — this feeds your honest impact log later.

### Phase 3 — SQL analytical layer
Star-schema in PostgreSQL: `dim_customer`, `dim_product`, `dim_company` (Trustpilot), `dim_category`, `dim_date`; facts: `fact_transaction`, `fact_review`, `fact_experiment_snapshot`. Demonstrate window functions, CTEs, ranking, cohort-style date logic, and at least one analytical view per module.

### Phase 4 — Statistical analysis (this is the phase most portfolio projects skip — don't)
This is where you prove you're a *scientist*, not just a model-fitter:
- **Hypothesis testing with assumption checks**: before any t-test/ANOVA/chi-square, check normality (Shapiro-Wilk or just QQ plots at this scale) and variance homogeneity (Levene's test); use Mann-Whitney/Kruskal-Wallis when assumptions fail.
- **Multiple comparisons correction**: when comparing satisfaction across 22 Trustpilot categories or dozens of product categories, you'll run many pairwise tests — apply Benjamini-Hochberg FDR correction and say so explicitly. (Skipping this is one of the most common — and most easily spotted — mistakes in junior DS portfolios.)
- **Effect sizes, not just p-values**: Cohen's d, Cramér's V, odds ratios — report these alongside significance.
- **Confidence intervals via bootstrapping** for skewed metrics (revenue per customer, review length) rather than assuming normality.
- **Regression diagnostics**: if you regress rating on price/category/etc., check residuals, multicollinearity (VIF), heteroscedasticity.

### Phase 5 — Customer Voice & serious NLP
Move well beyond "sentiment = 0.73":
- **Preprocessing**: standard English NLP pipeline (spaCy) — no Persian-specific normalisation needed now, but do handle contractions, emoji, and Trustpilot-specific noise.
- **Sentiment**: use a pretrained transformer (e.g. a DistilBERT/RoBERTa sentiment checkpoint from Hugging Face) rather than a lexicon-based score — and briefly compare it against a simple baseline (VADER or TF-IDF + logistic regression) so you can show you understand *why* the transformer wins, not just that it does.
- **Aspect-based sentiment**: extract what customers are talking about (delivery, packaging, price, customer service) and the sentiment *toward that aspect specifically*, not just overall review sentiment. This is the difference between "NLP for a coursework demo" and "NLP a retail marketing team can actually use."
- **Topic modelling**: BERTopic (embedding-based) instead of classic LDA — gives more coherent, more defensible-in-an-interview topics, and produces nice visualisations for your dashboard.
- **Keyword extraction**: KeyBERT or YAKE for per-category/per-company keyword summaries.
- **Explainable satisfaction-driver model**: a model predicting star rating (or recommend/not) from text + category + company features, explained with SHAP or LIME at both the aspect and word level — this connects NLP directly to Phase 7.

### Phase 6 — Behavioural ML: churn & CLV
On Online Retail II:
- Build RFM features, then a **churn label** (e.g. no purchase in the next N days after a cutoff date — pick N and justify it), split by **time**, not randomly, to avoid leakage.
- Model options: Logistic Regression (baseline, interpretable) → Gradient Boosting (LightGBM/XGBoost) for the "real" model. Evaluate with ROC-AUC, PR-AUC (churn is imbalanced), and calibration curves — a churn model with badly calibrated probabilities is a common failure UK interviewers specifically probe for.
- **CLV**: either a probabilistic model (BG/NBD + Gamma-Gamma via `lifetimes`) or a simpler regression-based proxy — be explicit about which you chose and why, since "which CLV approach and when" is itself a favourite interview question.

### Phase 7 — Explainability
Apply consistently across both ML models built in Phases 5 and 6:
- **Global**: SHAP summary plots, permutation importance.
- **Local**: SHAP waterfall/force plots for individual customer churn predictions and individual flagged reviews — this is what turns "we built a model" into "here's why the model flagged *this* customer/review," which is the language a marketing stakeholder actually needs.
- **Partial dependence / ICE plots** for key features (recency, price, category).
- One paragraph in your README on model limitations and where you would *not* trust the explanations (e.g. correlated features distorting SHAP attribution).

### Phase 8 — Experimentation & causal inference (the real differentiator)
Two parts, clearly labelled as separate:

**8a. Re-analysis of the real ASOS experiments** (no simulation needed here):
- Recompute effect sizes, confidence intervals, and p-values per experiment/metric from the aggregated statistics.
- Check the **distribution of p-values across all 78 experiments** — a well-known sanity check in this space (roughly a quarter of real experiments tend to show significant results; compare your finding against this and discuss what it implies about test quality/power in practice).
- Apply FDR correction across the multiple metrics tested per experiment and discuss how conclusions change.
- Look at effect heterogeneity across variants/time — do effects stabilise or drift over the observation window? (Relevant to novelty effects, a real practitioner concern.)

**8b. Design and power a *new* hypothetical experiment**, informed by your Phase 6 churn findings (e.g. "a targeted retention email for customers flagged as high-churn-risk"):
- State a primary metric, a minimum detectable effect, baseline conversion/retention rate, and compute required sample size/power properly (don't hand-wave this — show the formula or `statsmodels`/`scipy` power calculation).
- Simulate data under your assumptions **and label it clearly as simulated** in the README — never present simulated results as if they were observed. This honesty is exactly the kind of judgement a UK employer is testing for.
- Discuss guardrail metrics, ramp-up strategy, and what you'd need from engineering to actually run this (this shows you understand experimentation as an organisational process, not just a statistical test).

### Phase 9 — Power BI dashboards (trim to what earns its place)
Four dashboards is plenty for a personal project — don't over-build for its own sake:
1. **Executive Overview** — churn rate, CLV distribution, review volume, average sentiment, top/bottom categories.
2. **Customer Voice** — aspect-level sentiment, topic trends, flagged negative themes per category.
3. **Model & Explainability** — feature importance, example SHAP explanations for a handful of customers/reviews (screenshots pasted in, since SHAP itself doesn't render natively in Power BI).
4. **Experimentation** — the ASOS re-analysis results and your new experiment's power curve.

### Phase 10 — Deployment & cloud (kept intentionally small)
Given AWS's stronger presence in UK tech/e-commerce hiring specifically (vs. Azure's lead in enterprise/public sector), default to **AWS**:
- Containerise a small **FastAPI** service (`/predict_churn`, `/predict_clv`, `/explain`) with Docker.
- Store trained model artefacts and processed data extracts in **S3**.
- Deploy the API via **AWS App Runner** or **Elastic Beanstalk** (both sit comfortably in the free tier for a low-traffic personal project — avoid over-engineering into EKS/Kubernetes, which would be disproportionate for this project's traffic).
- Put a small **Streamlit** front end (hosted free on Streamlit Community Cloud or Hugging Face Spaces) in front of the API, so recruiters get a **clickable live demo link**, not just a repo.
- If you'd rather show Azure or GCP instead (equally valid, note the equivalents): Azure → Container Apps + Blob Storage; GCP → Cloud Run + Cloud Storage. Pick **one**, go deep, and say why in your README — "I chose AWS because X" is itself a good interview answer; scattering effort across three clouds is not.
- Add a minimal **GitHub Actions** workflow (lint + test on push) — cheap to add, disproportionately well-regarded.

### Phase 11 — Business recommendations & honest impact measurement
Keep the original's discipline exactly as written — it's genuinely good practice:
- Every recommendation follows Data → Insight → Business implication → Recommendation.
- **Never invent revenue/conversion impact this data can't support.** Measure what you can actually demonstrate: pipeline runtime vs. manual estimate, number of reviews auto-themed vs. manually read, model lift over a naive baseline, statistical power achieved. Keep `docs/impact_log.md` throughout, not retrofitted at the end.

### Phase 12 — How this gets attention on LinkedIn (new — this matters as much as the code)
- **Ship a live demo link**, not just a GitHub URL — this alone puts you ahead of most portfolio posts.
- Post as a **short thread/carousel**, not a wall of text: 1) the business question, 2) one striking chart (e.g. the SHAP explanation or the ASOS p-value distribution check), 3) the live demo link, 4) the repo.
- Lead with the **decision the analysis supports**, not the tool list — "identified the 8% of customers driving 40% of at-risk revenue" lands harder than "used LightGBM and SHAP."
- Name the project something memorable in the README header (e.g. *"RetainScope"* or similar) — small thing, but it reads as a product, not a homework assignment.

---

## 5. Technology stack (deliberately matched to UK job-posting language)

| Category | Tools |
|---|---|
| Core | Python, Pandas, NumPy, SQL |
| Statistics | SciPy, statsmodels, scikit-posthocs (for FDR correction) |
| ML | scikit-learn, LightGBM/XGBoost, `lifetimes` (CLV) |
| Explainability | SHAP, LIME |
| NLP | spaCy, Hugging Face Transformers, BERTopic, KeyBERT |
| Experimentation | statsmodels power analysis, custom power/FDR scripts |
| Data engineering | PostgreSQL, SQLAlchemy, Docker |
| BI | Power BI, DAX |
| Deployment/Cloud | FastAPI, Streamlit, Docker, AWS (S3, App Runner/Elastic Beanstalk), GitHub Actions |
| Dev practice | Git, GitHub, pytest, logging |

---

## 6. Suggested timeline (part-time, personal laptop, ~8–10 weeks)

| Weeks | Focus |
|---|---|
| 1 | Phase 0–1: setup, data profiling across all three datasets |
| 2 | Phase 2–3: ETL + Postgres analytical layer |
| 3 | Phase 4: statistical analysis (don't rush this — it's your differentiator) |
| 4–5 | Phase 5: NLP (sentiment, aspect-based, topic modelling) |
| 6 | Phase 6–7: churn/CLV model + SHAP explainability |
| 7 | Phase 8: ASOS re-analysis + new experiment design |
| 8 | Phase 9–10: Power BI + deployment |
| 9–10 | Phase 11–12: business write-up, impact log, README polish, LinkedIn launch |

---

## 7. Traps to avoid
- Don't force the three datasets into one artificial join — present them as three linked engagements instead.
- Don't skip assumption checks before hypothesis tests, and don't skip multiple-comparison correction — these are the fastest way a technical reviewer spots a shaky project.
- Don't present the simulated experiment as real data anywhere, including on LinkedIn.
- Don't claim revenue/business impact the data can't support.
- Don't spread cloud effort across AWS + Azure + GCP — pick one and justify it.
- Don't let Power BI dashboard count balloon past what genuinely earns its place — four focused dashboards beat eight shallow ones.
