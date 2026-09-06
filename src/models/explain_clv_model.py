import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import summary_data_from_transaction_data

# Reuse the same cleaned invoice-level data and full_summary as before —
# for simplicity, we re-run the same loading/cleaning steps here.
exec(open("src/models/train_clv_model.py").read().split("print(\"\\nRefitting")[0])

full_summary = summary_data_from_transaction_data(
    df, "customer_id", "invoice_date", monetary_value_col="invoice_value",
    observation_period_end=OBSERVATION_END, freq="D"
)
full_summary = full_summary[full_summary["frequency"] > 0].reset_index()

bgf_final = BetaGeoFitter(penalizer_coef=0.001)
bgf_final.fit(full_summary["frequency"], full_summary["recency"], full_summary["T"])
ggf_final = GammaGammaFitter(penalizer_coef=0.001)
ggf_final.fit(full_summary["frequency"], full_summary["monetary_value"])

feature_cols = ["frequency", "recency", "T", "monetary_value"]


def predict_clv(X):
    X = pd.DataFrame(X, columns=feature_cols)
    return ggf_final.customer_lifetime_value(
        bgf_final, X["frequency"], X["recency"], X["T"], X["monetary_value"],
        time=3, freq="D", discount_rate=0.0
    ).values


print("Sampling customers for SHAP (this method is slow, so we use a subset)...")
background = full_summary[feature_cols].sample(100, random_state=42)
sample_to_explain = full_summary[feature_cols].sample(200, random_state=42)

print("Computing SHAP values (this may take a few minutes)...")
explainer = shap.KernelExplainer(predict_clv, background)
shap_values = explainer.shap_values(sample_to_explain, nsamples=100)

os.makedirs("reports/figures", exist_ok=True)

base_values = np.full(shap_values.shape[0], explainer.expected_value)
shap_exp = shap.Explanation(
    values=shap_values, base_values=base_values,
    data=sample_to_explain.values, feature_names=feature_cols
)

shap.plots.bar(shap_exp, show=False)
plt.tight_layout()
plt.savefig("reports/figures/phase4_clv_shap_global_importance.png", dpi=150)
plt.close()
print("Saved: phase4_clv_shap_global_importance.png")

shap.plots.beeswarm(shap_exp, show=False)
plt.tight_layout()
plt.savefig("reports/figures/phase4_clv_shap_summary.png", dpi=150)
plt.close()
print("Saved: phase4_clv_shap_summary.png")

print("\nDone.")