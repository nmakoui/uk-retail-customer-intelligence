import pandas as pd

print("Reading raw ASOS experiments data...")
df = pd.read_csv("data/raw/asos/asos_digital_experiments_dataset.csv")
print(f"  Starting rows: {len(df)}")

# Drop rows with missing variance in either arm, or zero sample counts in either arm
before = len(df)
df_clean = df[
    df["variance_c"].notna()
    & df["variance_t"].notna()
    & (df["count_c"] != 0)
    & (df["count_t"] != 0)
].copy()

print(f"  Dropped: {before - len(df_clean)} rows")
print(f"  Remaining: {len(df_clean)} rows")

df_clean.to_csv("data/processed/asos_experiments_clean.csv", index=False)
print("Saved to data/processed/asos_experiments_clean.csv")