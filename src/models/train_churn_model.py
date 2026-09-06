import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import lightgbm as lgb

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

QUERY = """
WITH cutoff AS (
    SELECT DATE '2011-09-09' AS cutoff_date
),
calibration AS (
    SELECT
        t.customer_id,
        MIN(t.invoice_date)::date AS first_purchase_date,
        MAX(t.invoice_date)::date AS last_purchase_date,
        COUNT(DISTINCT t.invoice)  AS frequency,
        SUM(t.line_value)          AS monetary,
        BOOL_OR(t.is_cancellation) AS has_returned
    FROM transactions t, cutoff
    WHERE t.customer_id IS NOT NULL
      AND t.invoice_date < cutoff.cutoff_date
    GROUP BY t.customer_id
),
holdout_purchasers AS (
    SELECT DISTINCT t.customer_id
    FROM transactions t, cutoff
    WHERE t.customer_id IS NOT NULL
      AND t.invoice_date >= cutoff.cutoff_date
)
SELECT
    c.customer_id,
    (cutoff.cutoff_date - c.first_purchase_date)      AS tenure_days,
    (cutoff.cutoff_date - c.last_purchase_date)        AS recency_days,
    c.frequency,
    c.monetary,
    ROUND((c.monetary / c.frequency)::numeric, 2)      AS avg_order_value,
    c.has_returned,
    CASE WHEN h.customer_id IS NULL THEN 1 ELSE 0 END  AS churned
FROM calibration c
CROSS JOIN cutoff
LEFT JOIN holdout_purchasers h ON c.customer_id = h.customer_id
ORDER BY c.customer_id;
"""

print("Pulling feature table from the database...")
df = pd.read_sql(QUERY, engine)
print(f"  -> {len(df)} customers loaded")

feature_cols = ["tenure_days", "recency_days", "frequency", "monetary", "avg_order_value", "has_returned"]
X = df[feature_cols].copy()
X["has_returned"] = X["has_returned"].astype(int)
y = df["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")


def evaluate(name, y_true, y_pred, y_proba):
    print(f"\n--- {name} ---")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred):.3f}")
    print(f"Precision: {precision_score(y_true, y_pred):.3f}")
    print(f"Recall:    {recall_score(y_true, y_pred):.3f}")
    print(f"ROC-AUC:   {roc_auc_score(y_true, y_proba):.3f}")


# ---------- Baseline: Logistic Regression ----------
print("\nTraining baseline: Logistic Regression...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

log_reg = LogisticRegression(random_state=42)
log_reg.fit(X_train_scaled, y_train)
evaluate("Logistic Regression (baseline)", y_test,
          log_reg.predict(X_test_scaled), log_reg.predict_proba(X_test_scaled)[:, 1])

# ---------- LightGBM ----------
print("\nTraining LightGBM...")
lgb_model = lgb.LGBMClassifier(random_state=42)
lgb_model.fit(X_train, y_train)
evaluate("LightGBM", y_test,
          lgb_model.predict(X_test), lgb_model.predict_proba(X_test)[:, 1])

print("\nDone.")