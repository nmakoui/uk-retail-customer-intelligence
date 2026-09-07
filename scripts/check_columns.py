import pandas as pd

files = {
    "Online Retail II (transactions)": "data/processed/online_retail_all_clean.csv",
    "Online Retail II (customer/RFM)":  "data/processed/online_retail_customer_clean.csv",
    "Trustpilot Reviews":               "data/processed/trustpilot_reviews_clean.csv",
    "ASOS Experiments (raw - not yet re-exported clean)": "data/raw/asos/asos_digital_experiments_dataset.csv",
}

for name, path in files.items():
    print(f"\n=== {name} ===")
    df = pd.read_csv(path, nrows=5000)  # sample, since some files are large
    print(df.dtypes)
    print(df.head(2))