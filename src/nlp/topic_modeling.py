import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP

print("Loading the 10k stratified sample...")
df = pd.read_csv("data/processed/trustpilot_nlp_sample.csv")
df["full_text"] = (df["title"].fillna("") + ". " + df["review"].fillna("")).str.strip()
docs = df["full_text"].tolist()

print("Loading sentence embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Generating embeddings (progress bar below)...")
embeddings = embedding_model.encode(docs, show_progress_bar=True, batch_size=32)

# Fixed random_state for reproducibility, consistent with random_state=42 used
# throughout the rest of this project (churn/CLV train-test splits, etc.)
umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42)

print("\nFitting BERTopic (clustering the embeddings into topics)...")
topic_model = BERTopic(embedding_model=embedding_model, umap_model=umap_model, verbose=True, min_topic_size=30)
topics, probs = topic_model.fit_transform(docs, embeddings)

df["topic"] = topics

topic_info = topic_model.get_topic_info()
print(f"\nFound {len(topic_info) - 1} topics (plus an outlier group, topic -1, for reviews that didn't fit any cluster)")
print("\nTop 15 topics by size:")
print(topic_info.head(15)[["Topic", "Count", "Name"]])

os.makedirs("data/processed", exist_ok=True)
topic_info.to_csv("data/processed/trustpilot_topics_summary.csv", index=False)
df.to_csv("data/processed/trustpilot_topics_assigned.csv", index=False)

os.makedirs("models", exist_ok=True)
topic_model.save("models/bertopic_model", serialization="pickle")

print("\nSaved topic summary, per-review topic assignments, and the fitted model.")