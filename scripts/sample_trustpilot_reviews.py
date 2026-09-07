import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Pulling all reviews from the database...")
df = pd.read_sql("SELECT review_id, company_id, title, review, stars FROM reviews", engine)
print(f"  -> {len(df)} total reviews")

print("\nOriginal star rating distribution:")
print(df["stars"].value_counts(normalize=True).sort_index().round(3))

TARGET_N = 10000
sample_frac = TARGET_N / len(df)

sample = (
    df.groupby("stars", group_keys=False)
    .apply(lambda x: x.sample(frac=sample_frac, random_state=42))
    .reset_index(drop=True)
)

print(f"\nSampled {len(sample)} reviews.")
print("Sample star rating distribution (should closely match original):")
print(sample["stars"].value_counts(normalize=True).sort_index().round(3))

sample.to_csv("data/processed/trustpilot_nlp_sample.csv", index=False)
print("\nSaved to data/processed/trustpilot_nlp_sample.csv")