import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

print("Loading the 10k stratified sample...")
df = pd.read_csv("data/processed/trustpilot_nlp_sample.csv")
df["full_text"] = (df["title"].fillna("") + ". " + df["review"].fillna("")).str.strip()

# ---------- BASELINE: VADER ----------
print("Running VADER (baseline, rule-based)...")
analyzer = SentimentIntensityAnalyzer()
df["vader_compound"] = df["full_text"].apply(lambda t: analyzer.polarity_scores(t)["compound"])

def vader_to_bucket(score):
    if score <= -0.05:
        return "negative"
    elif score >= 0.05:
        return "positive"
    return "neutral"

df["vader_bucket"] = df["vader_compound"].apply(vader_to_bucket)

# ---------- TRANSFORMER: nlptown BERT (predicts 1-5 stars directly) ----------
print("Loading transformer model (this downloads ~700MB the first time)...")
sentiment_pipe = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    truncation=True,
    max_length=512,
)

print("Running transformer sentiment (this will take a while on CPU)...")
results = sentiment_pipe(df["full_text"].tolist(), batch_size=16)
df["bert_predicted_stars"] = [int(r["label"][0]) for r in results]  # label looks like "4 stars"

def stars_to_bucket(stars):
    if stars <= 2:
        return "negative"
    elif stars >= 4:
        return "positive"
    return "neutral"

df["actual_bucket"] = df["stars"].apply(stars_to_bucket)
df["bert_bucket"] = df["bert_predicted_stars"].apply(stars_to_bucket)

# ---------- COMPARISON ----------
vader_accuracy = (df["vader_bucket"] == df["actual_bucket"]).mean()
bert_accuracy = (df["bert_bucket"] == df["actual_bucket"]).mean()

print(f"\nVADER (baseline) accuracy vs actual star bucket: {vader_accuracy:.3f}")
print(f"Transformer accuracy vs actual star bucket:       {bert_accuracy:.3f}")

df.to_csv("data/processed/trustpilot_sentiment_comparison.csv", index=False)
print("\nSaved: data/processed/trustpilot_sentiment_comparison.csv")
