import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from tqdm import tqdm

print("Loading the 10k stratified sample...")
df = pd.read_csv("data/processed/trustpilot_nlp_sample.csv")
df["full_text"] = (df["title"].fillna("") + ". " + df["review"].fillna("")).str.strip()
docs = df["full_text"].tolist()

print("Loading sentence embedding model (same model used for topic modelling)...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model=embedding_model)

print("Extracting keyphrases per review (this takes a few minutes on 10k reviews)...")
all_keywords = []
batch_size = 200
for i in tqdm(range(0, len(docs), batch_size), desc="Keyword batches"):
    batch = docs[i:i + batch_size]
    batch_keywords = kw_model.extract_keywords(
        batch,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        use_mmr=True,
        diversity=0.5,
        top_n=5,
    )
    all_keywords.extend(batch_keywords)

# Each entry is a list of (phrase, score) tuples - keep just the phrases,
# joined into one string so this stays a flat CSV like the other Phase 5
# outputs. Split on " | " again when this goes into MongoDB as a real
# nested list in Phase 5.5.
df["keywords"] = [" | ".join(phrase for phrase, score in kw) for kw in all_keywords]

print("\nExample reviews with extracted keywords:")
print(df[["review_id", "stars", "keywords"]].sample(5, random_state=42).to_string(index=False))

os.makedirs("data/processed", exist_ok=True)
df[["review_id", "stars", "keywords"]].to_csv("data/processed/trustpilot_keywords.csv", index=False)
print("\nSaved: data/processed/trustpilot_keywords.csv")