import re
import pandas as pd
from tqdm import tqdm
from transformers import pipeline

print("Loading the 10k stratified sample...")
df = pd.read_csv("data/processed/trustpilot_nlp_sample.csv")
df["full_text"] = (df["title"].fillna("") + ". " + df["review"].fillna("")).str.strip()

ASPECT_KEYWORDS = {
    "delivery": ["delivery", "shipping", "arrived", "courier", "postage", "dispatch"],
    "customer_service": ["customer service", "support", "staff", "helpful", "rude", "responded"],
    "product_quality": ["quality", "broke", "faulty", "material", "cheaply made", "well made"],
    "price_value": ["price", "value", "expensive", "cheap", "worth it", "overpriced"],
    "returns_refunds": ["return", "refund", "exchange", "money back"],
}


def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', str(text))
    return [s.strip() for s in sentences if len(s.strip()) > 0]


print("Splitting reviews into sentences and matching aspect keywords...")
records = []
for _, row in tqdm(df.iterrows(), total=len(df), desc="Reviews"):
    for sentence in split_sentences(row["full_text"]):
        sentence_lower = sentence.lower()
        for aspect, keywords in ASPECT_KEYWORDS.items():
            if any(kw in sentence_lower for kw in keywords):
                records.append({
                    "review_id": row["review_id"],
                    "stars": row["stars"],
                    "aspect": aspect,
                    "sentence": sentence,
                })

aspect_df = pd.DataFrame(records)
print(f"\nFound {len(aspect_df)} aspect-mention sentences across {aspect_df['review_id'].nunique()} reviews")
print(aspect_df["aspect"].value_counts())

unique_sentences = aspect_df["sentence"].unique().tolist()
print(f"\n{len(unique_sentences)} unique sentences to score (deduplicated)")

print("\nLoading transformer model (already cached locally from last run)...")
sentiment_pipe = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    truncation=True,
    max_length=512,
)

print("Scoring sentiment for each unique sentence...")
batch_size = 16
sentence_to_stars = {}
for i in tqdm(range(0, len(unique_sentences), batch_size), desc="Sentiment batches"):
    batch = unique_sentences[i:i + batch_size]
    for sent, r in zip(batch, sentiment_pipe(batch)):
        sentence_to_stars[sent] = int(r["label"][0])

aspect_df["predicted_stars"] = aspect_df["sentence"].map(sentence_to_stars)

print("\n--- Aspect-level sentiment summary (lowest-scoring first) ---")
summary = aspect_df.groupby("aspect")["predicted_stars"].agg(["mean", "count"]).sort_values("mean")
print(summary.round(2))

aspect_df.to_csv("data/processed/trustpilot_aspect_sentiment.csv", index=False)
print("\nSaved: data/processed/trustpilot_aspect_sentiment.csv")