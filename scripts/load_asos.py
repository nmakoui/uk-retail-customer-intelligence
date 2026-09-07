import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}")

print("Reading cleaned ASOS data...")
df = pd.read_csv("data/processed/asos_experiments_clean.csv")

# ---------- EXPERIMENTS ----------
print("Building experiments table...")
experiments = df[["experiment_id"]].drop_duplicates().reset_index(drop=True)
print(f"  -> {len(experiments)} unique experiments")
experiments.to_sql("experiments", engine, if_exists="append", index=False)
print("  experiments loaded.")

# ---------- EXPERIMENT_RESULTS ----------
print("Loading experiment_results...")
results = df[[
    "experiment_id", "variant_id", "metric_id", "time_since_start",
    "count_c", "count_t", "mean_c", "mean_t", "variance_c", "variance_t"
]].copy()

results.to_sql(
    "experiment_results", engine, if_exists="append", index=False,
    chunksize=1000, method="multi"
)
print(f"  -> {len(results)} experiment_result rows loaded.")

print("Done.")