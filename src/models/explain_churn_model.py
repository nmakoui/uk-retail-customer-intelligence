import os
import pandas as pd
import matplotlib.pyplot as plt
import shap
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
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

df = pd.read_sql(QUERY, engine)
feature_cols = ["tenure_days", "recency_days", "frequency", "monetary", "avg_order_value", "has_returned"]
X = df[feature_cols].copy()
X["has_returned"] = X["has_returned"].astype(int)
y = df["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print("Training LightGBM...")
model = lgb.LGBMClassifier(random_state=42)
model.fit(X_train, y_train)

print("Computing SHAP values...")
explainer = shap.Explainer(model)
shap_values = explainer(X_test)

os.makedirs("reports/figures", exist_ok=True)

# Global: which features matter most, on average, across all customers
shap.plots.bar(shap_values, show=False)
plt.tight_layout()
plt.savefig("reports/figures/phase4_shap_global_importance.png", dpi=150)
plt.close()
print("Saved: phase4_shap_global_importance.png")

# Global: direction + spread — does each feature push churn up or down, and by how much
shap.plots.beeswarm(shap_values, show=False)
plt.tight_layout()
plt.savefig("reports/figures/phase4_shap_summary.png", dpi=150)
plt.close()
print("Saved: phase4_shap_summary.png")

# Local: explain one specific churned customer and one specific retained customer
churned_pos = y_test.reset_index(drop=True)[y_test.reset_index(drop=True) == 1].index[0]
retained_pos = y_test.reset_index(drop=True)[y_test.reset_index(drop=True) == 0].index[0]

shap.plots.waterfall(shap_values[churned_pos], show=False)
plt.tight_layout()
plt.savefig("reports/figures/phase4_shap_example_churned.png", dpi=150)
plt.close()
print("Saved: phase4_shap_example_churned.png")

shap.plots.waterfall(shap_values[retained_pos], show=False)
plt.tight_layout()
plt.savefig("reports/figures/phase4_shap_example_retained.png", dpi=150)
plt.close()
print("Saved: phase4_shap_example_retained.png")

print("\nDone. Check reports/figures/ for all 4 plots.")