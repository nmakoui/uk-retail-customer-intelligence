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

print("Reading cleaned Online Retail II data...")
df = pd.read_csv("data/processed/online_retail_all_clean.csv")
df["invoice_date"] = pd.to_datetime(df["invoice_date"])


def most_frequent(series):
    """Return the most common non-missing value; alphabetically first if tied."""
    series = series.dropna()
    if len(series) == 0:
        return "UNKNOWN"
    return series.mode().sort_values().iloc[0]


# ---------- PRODUCTS ----------
print("Building products table (most frequent description per stock_code)...")
products = df.groupby("stock_code")["description"].apply(most_frequent).reset_index()
print(f"  -> {len(products)} unique products")
products.to_sql("products", engine, if_exists="append", index=False)
print("  products loaded.")

# ---------- CUSTOMERS ----------
print("Building customers table (most frequent country per customer_id)...")
cust_df = df[df["customer_id"].notna()].copy()
cust_df["customer_id"] = cust_df["customer_id"].astype(int)
customers = cust_df.groupby("customer_id")["country"].apply(most_frequent).reset_index()
print(f"  -> {len(customers)} unique customers")
customers.to_sql("customers", engine, if_exists="append", index=False)
print("  customers loaded.")

# ---------- TRANSACTIONS ----------
print("Loading transactions (~1M rows, this will take a few minutes)...")
transactions = df[[
    "invoice", "stock_code", "customer_id", "invoice_date",
    "quantity", "price", "line_value", "country",
    "is_cancellation", "is_product", "is_zero_value"
]].copy()
transactions["customer_id"] = transactions["customer_id"].astype("Int64")  # nullable integer

transactions.to_sql(
    "transactions", engine, if_exists="append", index=False,
    chunksize=1000, method="multi"
)
print(f"  -> {len(transactions)} transaction rows loaded.")

print("Done.")