import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Loading topic assignments...")
topics_df = pd.read_csv("data/processed/trustpilot_topics_assigned.csv")

print("Pulling real company categories from the database...")
companies = pd.read_sql("SELECT company_id, category FROM companies", engine)

df = topics_df.merge(companies, on="company_id", how="left")
topic_summary = pd.read_csv("data/processed/trustpilot_topics_summary.csv")

print("\n--- Category concentration per topic (top 16, including outlier group) ---")
results = []
for topic_id in topic_summary.sort_values("Count", ascending=False).head(16)["Topic"]:
    subset = df[df["topic"] == topic_id]
    if len(subset) == 0:
        continue
    cat_counts = subset["category"].value_counts(normalize=True)
    results.append({
        "topic": topic_id,
        "count": len(subset),
        "dominant_category": cat_counts.index[0],
        "dominant_pct": round(cat_counts.iloc[0], 3),
        "n_unique_categories": subset["category"].nunique(),
    })

result_df = pd.DataFrame(results)
print(result_df.to_string(index=False))

result_df.to_csv("data/processed/trustpilot_topic_category_validation.csv", index=False)
print("\nSaved: data/processed/trustpilot_topic_category_validation.csv")