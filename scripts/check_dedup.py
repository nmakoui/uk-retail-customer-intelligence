import pandas as pd

df = pd.read_csv("data/processed/online_retail_all_clean.csv")

# How many stock codes have more than one distinct description?
desc_counts = df.groupby("stock_code")["description"].nunique()
messy_products = (desc_counts > 1).sum()
print(f"Stock codes with >1 distinct description: {messy_products} out of {len(desc_counts)}")

# How many customers have more than one distinct country?
cust_df = df[df["customer_id"].notna()]
country_counts = cust_df.groupby("customer_id")["country"].nunique()
messy_customers = (country_counts > 1).sum()
print(f"Customers with >1 distinct country: {messy_customers} out of {len(country_counts)}")

# Trustpilot: does each company have a single, consistent category/description?
tp = pd.read_csv("data/processed/trustpilot_reviews_clean.csv")
cat_counts = tp.groupby("company")["category"].nunique()
desc_counts_tp = tp.groupby("company")["description"].nunique()
print(f"Companies with >1 distinct category: {(cat_counts > 1).sum()} out of {len(cat_counts)}")
print(f"Companies with >1 distinct description: {(desc_counts_tp > 1).sum()} out of {len(desc_counts_tp)}")
