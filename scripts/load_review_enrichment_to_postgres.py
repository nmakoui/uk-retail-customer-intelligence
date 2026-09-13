import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("Clearing existing rows (safe to rerun this script)...")
with engine.begin() as conn:
    conn.execute(text(
        "TRUNCATE TABLE review_keywords, review_aspects, review_sentiment "
        "RESTART IDENTITY CASCADE"
    ))

print("Loading Phase 5 outputs...")
sentiment = pd.read_csv("data/processed/trustpilot_sentiment_comparison.csv")
aspects = pd.read_csv("data/processed/trustpilot_aspect_sentiment.csv")
topics = pd.read_csv("data/processed/trustpilot_topics_assigned.csv")
topic_labels = pd.read_csv("data/processed/trustpilot_topics_summary.csv")
keywords = pd.read_csv("data/processed/trustpilot_keywords.csv")

topic_name_by_id = topic_labels.set_index("Topic")["Name"].to_dict()
topic_name_by_id[-1] = "no_coherent_topic (outlier)"

# ---------- review_sentiment (one row per review) ----------
print("Building review_sentiment...")
sentiment_table = sentiment[["review_id", "vader_compound", "vader_bucket",
                              "bert_predicted_stars", "bert_bucket"]].copy()
sentiment_table = sentiment_table.merge(
    topics[["review_id", "topic"]], on="review_id", how="left"
).rename(columns={"topic": "topic_id"})
sentiment_table["topic_label"] = sentiment_table["topic_id"].map(topic_name_by_id)

sentiment_table.to_sql("review_sentiment", engine, if_exists="append", index=False)
print(f"  -> {len(sentiment_table)} rows loaded into review_sentiment.")

# ---------- review_aspects (zero-to-many rows per review) ----------
print("Building review_aspects...")
aspects_table = aspects[["review_id", "aspect", "sentence", "predicted_stars"]]
aspects_table.to_sql("review_aspects", engine, if_exists="append", index=False)
print(f"  -> {len(aspects_table)} rows loaded into review_aspects "
      f"(covering {aspects_table['review_id'].nunique()} distinct reviews).")

# ---------- review_keywords (up to ~5 rows per review) ----------
print("Building review_keywords...")
keywords_long = keywords.dropna(subset=["keywords"]).copy()
# Plain Python .split() here, not pandas' .str.split() - "|" is a regex
# metacharacter, so .str.split(" | ") silently splits on every space
# instead of the literal " | " separator. .apply() with a lambda calls
# Python's built-in str.split(), which is never regex.
keywords_long["keyword"] = keywords_long["keywords"].apply(lambda s: s.split(" | "))
keywords_long = keywords_long.explode("keyword")[["review_id", "keyword"]]
keywords_long.to_sql("review_keywords", engine, if_exists="append", index=False)
print(f"  -> {len(keywords_long)} rows loaded into review_keywords.")

print("\nDone.")