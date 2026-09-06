import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from lifetimes.utils import calibration_and_holdout_data
from lifetimes import BetaGeoFitter
from lifetimes import ParetoNBDFitter
from lifetimes import GammaGammaFitter
from scipy.stats import pearsonr

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

QUERY = """
WITH invoices AS (
    SELECT
        customer_id,
        invoice,
        MIN(invoice_date) AS invoice_date,
        SUM(line_value)   AS invoice_value,
        BOOL_OR(is_cancellation) AS is_cancellation
    FROM transactions
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, invoice
)
SELECT customer_id, invoice, invoice_date, invoice_value, is_cancellation
FROM invoices
ORDER BY customer_id, invoice_date;
"""

print("Pulling invoice-level data...")
df = pd.read_sql(QUERY, engine)
df["invoice_date"] = pd.to_datetime(df["invoice_date"])
print("Checking for same-day, fully-reversed orders (likely data-entry errors)...")
df["day"] = df["invoice_date"].dt.date

exclude_invoices = set()
for (cust, day), group in df.groupby(["customer_id", "day"]):
    if len(group) < 2:
        continue
    values = group["invoice_value"].values
    invoices = group["invoice"].values
    for i in range(len(values)):
        for j in range(len(values)):
            if i != j and values[i] > 0 and abs(values[i] + values[j]) < 0.01:
                exclude_invoices.add(invoices[i])
                exclude_invoices.add(invoices[j])

print(f"  -> Found {len(exclude_invoices)} invoices involved in same-day full reversals (excluded)")

df = df[~df["invoice"].isin(exclude_invoices)]
df = df[df["is_cancellation"] == False]  # drop any remaining, non-fully-matched cancellations, as before
df = df.drop(columns=["is_cancellation", "day"])

print(f"  -> {len(df)} genuine invoices remain across {df['customer_id'].nunique()} customers")
print(f"  -> {len(df)} genuine invoices across {df['customer_id'].nunique()} customers")

CALIBRATION_END = pd.Timestamp("2011-09-09")
OBSERVATION_END = df["invoice_date"].max()

print("\nBuilding calibration/holdout summary (frequency, recency, T per customer)...")
cal_holdout = calibration_and_holdout_data(
    transactions=df,
    customer_id_col="customer_id",
    datetime_col="invoice_date",
    calibration_period_end=CALIBRATION_END,
    observation_period_end=OBSERVATION_END,
    freq="D",
    monetary_value_col="invoice_value",
)
print(f"  -> {len(cal_holdout)} customers with usable history")
print(cal_holdout.head())

print("\nFitting BG/NBD on the calibration period...")
bgf = BetaGeoFitter(penalizer_coef=0.001)
bgf.fit(cal_holdout["frequency_cal"], cal_holdout["recency_cal"], cal_holdout["T_cal"])
print(bgf.summary)

print("\nValidating: predicted vs. actual repeat purchases in the holdout window...")
cal_holdout["predicted_purchases"] = bgf.predict(
    cal_holdout["duration_holdout"],
    cal_holdout["frequency_cal"],
    cal_holdout["recency_cal"],
    cal_holdout["T_cal"],
)

total_predicted = cal_holdout["predicted_purchases"].sum()
total_actual = cal_holdout["frequency_holdout"].sum()
corr, p_value = pearsonr(cal_holdout["predicted_purchases"], cal_holdout["frequency_holdout"])

print(f"  Total predicted repeat purchases (holdout): {total_predicted:.1f}")
print(f"  Total actual repeat purchases (holdout):    {total_actual:.0f}")
print(f"  Correlation (predicted vs actual, per customer): {corr:.3f} (p={p_value:.4f})")

print("\nFitting Pareto/NBD on the calibration period...")
pnbd = ParetoNBDFitter(penalizer_coef=0.001)
pnbd.fit(cal_holdout["frequency_cal"], cal_holdout["recency_cal"], cal_holdout["T_cal"])
print(pnbd.params_)

cal_holdout["predicted_purchases_pnbd"] = pnbd.predict(
    cal_holdout["duration_holdout"],
    cal_holdout["frequency_cal"],
    cal_holdout["recency_cal"],
    cal_holdout["T_cal"],
)

total_predicted_pnbd = cal_holdout["predicted_purchases_pnbd"].sum()
corr_pnbd, p_value_pnbd = pearsonr(
    cal_holdout["predicted_purchases_pnbd"], cal_holdout["frequency_holdout"]
)

print("\n--- Model comparison ---")
print(f"{'Model':<12} {'Predicted':>12} {'Actual':>10} {'Correlation':>12}")
print(f"{'BG/NBD':<12} {total_predicted:>12.1f} {total_actual:>10.0f} {corr:>12.3f}")
print(f"{'Pareto/NBD':<12} {total_predicted_pnbd:>12.1f} {total_actual:>10.0f} {corr_pnbd:>12.3f}")

print("\nChecking Gamma-Gamma's independence assumption...")
repeat_customers = cal_holdout[cal_holdout["frequency_cal"] > 0]
assumption_corr, assumption_p = pearsonr(
    repeat_customers["frequency_cal"], repeat_customers["monetary_value_cal"]
)
print(f"  Correlation between frequency and average order value: {assumption_corr:.3f} (p={assumption_p:.4f})")

print("\nFitting Gamma-Gamma...")
ggf = GammaGammaFitter(penalizer_coef=0.001)
ggf.fit(repeat_customers["frequency_cal"], repeat_customers["monetary_value_cal"])
print(ggf.summary)

cal_holdout.to_csv("data/processed/clv_calibration_holdout.csv")
print("\nSaved calibration/holdout table for the next step.")

print("\nRefitting BG/NBD and Gamma-Gamma on ALL data (no holdout this time)...")

from lifetimes.utils import summary_data_from_transaction_data

full_summary = summary_data_from_transaction_data(
    df, "customer_id", "invoice_date", monetary_value_col="invoice_value",
    observation_period_end=OBSERVATION_END, freq="D"
)
full_summary = full_summary[full_summary["frequency"] > 0]  # Gamma-Gamma needs repeat purchasers

bgf_final = BetaGeoFitter(penalizer_coef=0.001)
bgf_final.fit(full_summary["frequency"], full_summary["recency"], full_summary["T"])

ggf_final = GammaGammaFitter(penalizer_coef=0.001)
ggf_final.fit(full_summary["frequency"], full_summary["monetary_value"])

print("Predicting 3-month forward CLV per customer...")
full_summary["predicted_clv_3m"] = ggf_final.customer_lifetime_value(
    bgf_final,
    full_summary["frequency"],
    full_summary["recency"],
    full_summary["T"],
    full_summary["monetary_value"],
    time=3,          # months
    freq="D",
    discount_rate=0.0,  # no time-value-of-money discounting — a simplifying assumption, worth noting
)

print(full_summary[["frequency", "recency", "T", "monetary_value", "predicted_clv_3m"]]
      .sort_values("predicted_clv_3m", ascending=False).head(10))

full_summary.to_csv("data/processed/clv_final_predictions.csv")
print(f"\nSaved final CLV predictions for {len(full_summary)} customers.")