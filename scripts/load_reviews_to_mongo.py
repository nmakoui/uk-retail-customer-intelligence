import os
import json
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

print("Loading Phase 5 outputs...")
base = pd.read_csv("data/processed/trustpilot_nlp_sample.csv")
sentiment = pd.read_csv("data/processed/trustpilot_sentiment_comparison.csv")
aspects = pd.read_csv("data/processed/trustpilot_aspect_sentiment.csv")
topics = pd.read_csv("data/processed/trustpilot_topics_assigned.csv")
topic_labels = pd.read_csv("data/processed/trustpilot_topics_summary.csv")
keywords = pd.read_csv("data/processed/trustpilot_keywords.csv")

print(f"Base sample: {len(base)} reviews")
print(f"Reviews with at least one matched aspect: {aspects['review_id'].nunique()} "
      f"({aspects['review_id'].nunique() / len(base):.1%}) - the rest get an empty "
      f"aspects list, which is exactly the variable-shape case Mongo handles naturally.")

sentiment_lookup = sentiment.set_index("review_id")[
    ["vader_compound", "vader_bucket", "bert_predicted_stars", "bert_bucket"]
].to_dict(orient="index")

topic_name_by_id = topic_labels.set_index("Topic")["Name"].to_dict()
topic_lookup = topics.set_index("review_id")["topic"].to_dict()

# Genuinely long format - group into a list per review
aspects_lookup = {}
for review_id, group in aspects.groupby("review_id"):
    aspects_lookup[review_id] = group[["aspect", "sentence", "predicted_stars"]].to_dict(orient="records")

keywords_lookup = keywords.set_index("review_id")["keywords"].to_dict()

print("Building one document per review...")
documents = []
for _, row in base.iterrows():
    review_id = int(row["review_id"])
    topic_id = int(topic_lookup.get(review_id, -1))
    kw_string = keywords_lookup.get(review_id)
    documents.append({
        "_id": review_id,
        "company_id": int(row["company_id"]),
        "title": row["title"],
        "review": row["review"],
        "stars": int(row["stars"]),
        "sentiment": sentiment_lookup.get(review_id, {}),
        "aspects": aspects_lookup.get(review_id, []),
        "topic": {
            "topic_id": topic_id,
            "topic_label": topic_name_by_id.get(topic_id, "unknown"),
        },
        "keywords": kw_string.split(" | ") if pd.notna(kw_string) else [],
    })

print(f"Built {len(documents)} documents.")

# Sanity check before writing anything - one review with aspects, one without,
# so we can eyeball the shape is right before loading everything.
has_aspects = next(d for d in documents if len(d["aspects"]) > 0)
no_aspects = next(d for d in documents if len(d["aspects"]) == 0)
print("\n--- Example WITH aspects ---")
print(json.dumps(has_aspects, indent=2, default=str)[:1200])
print("\n--- Example WITHOUT aspects (empty list, not a missing field) ---")
print(json.dumps(no_aspects, indent=2, default=str)[:800])

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
collection = db["reviews"]

print(f"\nClearing any existing documents in '{collection.name}' (safe to rerun this script)...")
collection.delete_many({})

print("Inserting documents...")
collection.insert_many(documents)
print(f"Inserted {collection.count_documents({})} documents into MongoDB.")