"""
Tests use a small, hand-crafted dataframe covering each specific edge case
found in the real data, rather than the full 1M-row file - so these run
in under a second and clearly document what each rule is supposed to do.
"""
import pandas as pd
import pytest

from src.data_engineering.online_retail_cleaning import clean_online_retail


@pytest.fixture
def raw_sample() -> pd.DataFrame:
    rows = [
        # a normal, valid sale with a customer attached
        dict(invoice="500001", stock_code="85048", description="GLASS BALL",
             quantity=12, invoice_date="2010-01-01", price=6.95, customer_id=1001.0, country="United Kingdom"),
        # exact duplicate of the row above -> should be removed
        dict(invoice="500001", stock_code="85048", description="GLASS BALL",
             quantity=12, invoice_date="2010-01-01", price=6.95, customer_id=1001.0, country="United Kingdom"),
        # a genuine cancellation/return -> should be KEPT
        dict(invoice="C500002", stock_code="85048", description="GLASS BALL",
             quantity=-2, invoice_date="2010-01-02", price=6.95, customer_id=1001.0, country="United Kingdom"),
        # a valid sale with NO customer id -> kept in "all", dropped from "customer" view
        dict(invoice="500003", stock_code="22041", description="RECORD FRAME",
             quantity=48, invoice_date="2010-01-03", price=2.10, customer_id=None, country="United Kingdom"),
        # a junk row: negative price, bad debt adjustment -> removed entirely
        dict(invoice="A500004", stock_code="B", description="Adjust bad debt",
             quantity=1, invoice_date="2010-01-04", price=-100.0, customer_id=None, country="United Kingdom"),
        # a junk row: zero price with a junk description -> removed entirely
        dict(invoice="500005", stock_code="22042", description="damaged",
             quantity=1, invoice_date="2010-01-05", price=0.0, customer_id=1002.0, country="United Kingdom"),
        # a literal test entry -> removed entirely
        dict(invoice="500006", stock_code="TEST001", description="This is a test",
             quantity=1, invoice_date="2010-01-06", price=1.0, customer_id=1003.0, country="United Kingdom"),
        # a non-product charge code (postage) -> KEPT, flagged is_product=False
        dict(invoice="500007", stock_code="POST", description="POSTAGE",
             quantity=1, invoice_date="2010-01-07", price=15.0, customer_id=1003.0, country="United Kingdom"),
    ]
    return pd.DataFrame(rows)


def test_duplicates_are_removed(raw_sample):
    all_clean, _, report = clean_online_retail(raw_sample)
    assert report.duplicates_removed == 1
    # only one of the two identical rows should survive
    matching = all_clean[(all_clean.invoice == "500001") & (all_clean.stock_code == "85048")]
    assert len(matching) == 1


def test_cancellations_are_kept_and_flagged(raw_sample):
    all_clean, customer_clean, report = clean_online_retail(raw_sample)
    cancel_row = all_clean[all_clean.invoice == "C500002"]
    assert len(cancel_row) == 1
    assert bool(cancel_row.iloc[0]["is_cancellation"]) is True
    assert cancel_row.iloc[0]["quantity"] == -2
    assert report.cancellation_rows_kept == 1


def test_missing_customer_id_kept_in_all_but_not_customer_view(raw_sample):
    all_clean, customer_clean, report = clean_online_retail(raw_sample)
    assert (all_clean.invoice == "500003").any()          # present in "all"
    assert not (customer_clean.invoice == "500003").any()  # absent from "customer"
    assert report.rows_missing_customer_id >= 1


def test_junk_rows_removed_entirely(raw_sample):
    all_clean, _, report = clean_online_retail(raw_sample)
    assert not (all_clean.invoice == "A500004").any()  # bad debt row gone
    assert not (all_clean.invoice == "500005").any()   # "damaged" row gone
    assert report.junk_rows_removed == 2


def test_test_entries_removed(raw_sample):
    all_clean, _, report = clean_online_retail(raw_sample)
    assert not (all_clean.stock_code == "TEST001").any()
    assert report.test_rows_removed == 1


def test_non_product_codes_kept_but_flagged(raw_sample):
    all_clean, _, report = clean_online_retail(raw_sample)
    post_row = all_clean[all_clean.stock_code == "POST"]
    assert len(post_row) == 1
    assert bool(post_row.iloc[0]["is_product"]) is False
    assert report.non_product_rows_flagged == 1


def test_line_value_computed_correctly(raw_sample):
    all_clean, _, _ = clean_online_retail(raw_sample)
    row = all_clean[all_clean.invoice == "500001"].iloc[0]
    assert row["line_value"] == pytest.approx(12 * 6.95)
    # a return's line_value should be negative (negative quantity)
    cancel_row = all_clean[all_clean.invoice == "C500002"].iloc[0]
    assert cancel_row["line_value"] < 0


def test_row_counts_are_consistent(raw_sample):
    all_clean, customer_clean, report = clean_online_retail(raw_sample)
    assert report.rows_before == len(raw_sample)
    assert report.rows_after_all == len(all_clean)
    assert report.rows_after_customer_level == len(customer_clean)
    assert len(customer_clean) <= len(all_clean)
