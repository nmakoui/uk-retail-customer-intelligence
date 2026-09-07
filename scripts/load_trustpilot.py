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

print("Reading cleaned Trustpilot data...")
df = pd.read_csv("data/processed/trustpilot_reviews_clean.csv")

# ---------- COMPANIES ----------
print("Building companies table...")
companies = df[["company", "category", "description"]].drop_duplicates(subset="company").reset_index(drop=True)
print(f"  -> {len(companies)} unique companies")
companies.to_sql("companies", engine, if_exists="append", index=False)
print("  companies loaded.")

# ---------- REVIEWS ----------
print("Loading reviews, linking each to its company_id...")
# Pull back the company_id values Postgres just generated, so reviews can reference them
company_lookup = pd.read_sql("SELECT company_id, company FROM companies", engine)

reviews = df.merge(company_lookup, on="company", how="left")[
    ["company_id", "title", "review", "stars"]
]

reviews.to_sql(
    "reviews", engine, if_exists="append", index=False,
    chunksize=1000, method="multi"
)
print(f"  -> {len(reviews)} review rows loaded.")

print("Done.")
