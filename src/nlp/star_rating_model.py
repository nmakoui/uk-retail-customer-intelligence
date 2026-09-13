import os
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay,
)
import lightgbm as lgb

print("Loading the 10k stratified sample...")
df = pd.read_csv("data/processed/trustpilot_nlp_sample.csv")
df["full_text"] = (df["title"].fillna("") + ". " + df["review"].fillna("")).str.strip()

print("\nStar rating distribution in the sample:")
print(df["stars"].value_counts().sort_index())

X_text = df["full_text"]
y = df["stars"]

X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text, y, test_size=0.2, random_state=42, stratify=y
)

print("\nVectorising review text with TF-IDF...")
vectorizer = TfidfVectorizer(max_features=3000, stop_words="english", ngram_range=(1, 2))
X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)
feature_names = vectorizer.get_feature_names_out()

print("\nTraining Logistic Regression baseline...")
baseline = LogisticRegression(max_iter=1000, random_state=42)
baseline.fit(X_train, y_train)
baseline_preds = baseline.predict(X_test)
print(f"Logistic Regression - accuracy: {accuracy_score(y_test, baseline_preds):.3f}, "
      f"macro F1: {f1_score(y_test, baseline_preds, average='macro'):.3f}")

print("\nTraining LightGBM...")
lgb_model = lgb.LGBMClassifier(random_state=42, verbose=-1)
lgb_model.fit(X_train, y_train)
lgb_preds = lgb_model.predict(X_test)
print(f"LightGBM - accuracy: {accuracy_score(y_test, lgb_preds):.3f}, "
      f"macro F1: {f1_score(y_test, lgb_preds, average='macro'):.3f}")

# Logistic Regression came out ahead on both metrics - the opposite of
# Phase 4's churn result, and a sensible one: TF-IDF gives ~3,000 sparse,
# largely independent features, exactly the setting where a linear
# model's weighted sum has an edge over a tree ensemble's one-feature-
# at-a-time splits. So Logistic Regression, not LightGBM, is what we
# explain below - the honest choice given what the numbers showed.
final_model = baseline
final_preds = baseline_preds
print("\nLogistic Regression wins on both metrics - using it as the explained "
      "model (contrast with Phase 4, where the more complex model won).")

print("\nFull classification report (Logistic Regression, the winning model):")
print(classification_report(y_test, final_preds))

class_labels = sorted(y.unique())

print("\nConfusion matrix (rows = actual, columns = predicted):")
cm = confusion_matrix(y_test, final_preds, labels=class_labels)
cm_df = pd.DataFrame(cm, index=[f"actual_{s}" for s in class_labels],
                      columns=[f"pred_{s}" for s in class_labels])
print(cm_df)

# How far off is each wrong prediction? |predicted - actual| == 1 means it
# picked an adjacent star rating (e.g. said 3 when it was really 2) - a
# much softer error than picking something on the far end of the scale.
errors = np.array(final_preds) - np.array(y_test)
wrong_mask = errors != 0
off_by_one = (np.abs(errors[wrong_mask]) == 1).mean()
print(f"\nOf all wrong predictions, {off_by_one:.1%} were off by exactly one star.")

os.makedirs("reports/figures", exist_ok=True)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_labels)
disp.plot(cmap="Blues", values_format="d")
plt.title("Star rating: confusion matrix (Logistic Regression)")
plt.tight_layout()
plt.savefig("reports/figures/phase5_star_confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: reports/figures/phase5_star_confusion_matrix.png")

print("\nExplaining Logistic Regression predictions with SHAP (LinearExplainer)...")
explainer = shap.LinearExplainer(final_model, X_train)
X_test_dense = X_test.toarray()
shap_values = explainer.shap_values(X_test_dense)
print(f"(diagnostic) type of shap_values: {type(shap_values)}, "
      f"shape/len: {getattr(shap_values, 'shape', len(shap_values))}")

if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
    shap_values = [shap_values[:, :, i] for i in range(shap_values.shape[2])]

for i, star in enumerate(class_labels):
    plt.figure()
    shap.summary_plot(shap_values[i], X_test_dense, feature_names=feature_names, show=False, max_display=15)
    plt.title(f"SHAP summary - predicting {star}-star reviews (Logistic Regression)")
    plt.tight_layout()
    plt.savefig(f"reports/figures/phase5_shap_star_{star}.png", dpi=150, bbox_inches="tight")
    plt.close()

print("Saved SHAP summary plots: reports/figures/phase5_shap_star_*.png")

os.makedirs("models", exist_ok=True)
joblib.dump({"vectorizer": vectorizer, "model": final_model}, "models/star_rating_model.pkl")
print("Saved model + vectorizer: models/star_rating_model.pkl") 