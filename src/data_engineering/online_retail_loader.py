"""
online_retail_loader.py
-------------------------
Loads the raw Online Retail II CSV (UCI ML Repository / Kaggle mirror:
mashlyn/online-retail-ii-uci).

Raw columns, as published:
    Invoice, StockCode, Description, Quantity, InvoiceDate, Price,
    Customer ID, Country

We rename to snake_case for consistency with the rest of the project and
parse dates/types properly. No cleaning decisions happen in this file -
see online_retail_cleaning.py for that. Keeping "load" and "clean"
separate means we can always re-inspect the untouched raw data later.
"""

from __future__ import annotations

import pandas as pd

RAW_PATH = "data/raw/online_retail/online_retail_II.csv"

COLUMN_RENAME = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}


def load_raw(path: str = RAW_PATH) -> pd.DataFrame:
    """Load the raw CSV exactly as published, just with sane column names
    and dtypes. The file uses a non-UTF8 encoding for a few special
    characters (e.g. in "PINK CHERRY LIGHTS" style descriptions with
    quote marks), so we read it with 'unicode_escape' rather than the
    default, which otherwise raises a UnicodeDecodeError partway through
    the file.
    """
    df = pd.read_csv(path, encoding="unicode_escape")
    df = df.rename(columns=COLUMN_RENAME)
    df["invoice"] = df["invoice"].astype(str)
    df["stock_code"] = df["stock_code"].astype(str)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    return df
