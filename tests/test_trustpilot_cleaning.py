import pandas as pd
import pytest

from src.data_engineering.trustpilot_cleaning import clean_trustpilot


@pytest.fixture
def raw_sample() -> pd.DataFrame:
    rows = [
        dict(category="Shopping & Fashion", company="example.co.uk",
             description="We sell things.", title="Great service",
             review="Really happy with the quick delivery and helpful staff.",
             stars=5),
        dict(category="Shopping & Fashion", company="example.co.uk",
             description="We sell things.", title="Bit pricey",
             review="Far too expensive", stars=2),  # short but genuine - must be KEPT
        dict(category="Money & Insurance", company="phonelookalike.co.uk",
             description="Finance company.", title="review",
             review="01959312890", stars=1),  # phone number - remove
        dict(category="Construction & Manufacturing", company="builders.co.uk",
             description="We build things.", title="meh",
             review="...........", stars=3),  # punctuation only - remove
        dict(category="Travel & Vacation", company="greekco.com",
             description="Travel agency.", title="oxi",
             review="γνωρησα ανθρωπους που ηταν με αλον τροπο", stars=4),  # non-English - remove
        dict(category="Shopping & Fashion", company="example.co.uk",
             description="We sell things.", title="Great service",
             review="Really happy with the quick delivery and helpful staff.",
             stars=5),  # exact duplicate of row 0 - remove
    ]
    return pd.DataFrame(rows)


def test_short_but_genuine_review_is_kept(raw_sample):
    clean, report = clean_trustpilot(raw_sample)
    assert (clean["review"] == "Far too expensive").any()


def test_phone_number_review_removed(raw_sample):
    clean, report = clean_trustpilot(raw_sample)
    assert not (clean["review"] == "01959312890").any()
    assert report.phone_number_rows_removed == 1


def test_punctuation_only_review_removed(raw_sample):
    clean, report = clean_trustpilot(raw_sample)
    assert not (clean["review"] == "...........").any()
    assert report.punctuation_only_rows_removed == 1


def test_non_english_review_removed(raw_sample):
    clean, report = clean_trustpilot(raw_sample)
    assert not clean["review"].str.contains("γνωρησα").any()
    assert report.non_english_rows_removed == 1


def test_exact_duplicate_removed(raw_sample):
    clean, report = clean_trustpilot(raw_sample)
    assert report.duplicates_removed == 1
    matching = clean[clean["review"].str.contains("Really happy with the quick delivery")]
    assert len(matching) == 1


def test_row_counts_consistent(raw_sample):
    clean, report = clean_trustpilot(raw_sample)
    assert report.rows_before == len(raw_sample)
    assert report.rows_after == len(clean)
    # 1 exact dup + 1 phone + 1 punctuation + 1 non-english = 4 removed, 2 remain
    assert report.rows_after == 2
