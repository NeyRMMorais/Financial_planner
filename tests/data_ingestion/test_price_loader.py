"""Unit tests for the base pricing loader and validation rules."""

from __future__ import annotations

from decimal import Decimal
from io import StringIO
import pandas as pd
import pytest

from src.financial_planner.data_ingestion.price_loader import load_pricing_data
from src.financial_planner.data_ingestion.validation import PlanningValidationError


def test_load_pricing_data_happy_path() -> None:
    """The default mock pricing CSV should load and parse prices to Decimals."""

    price_df = load_pricing_data()

    # Reconcile counts
    assert len(price_df) == 60  # 5 materials * 6 customers * 2 ship-tos per customer
    assert list(price_df.columns) == [
        "Sold to ID",
        "Ship to ID",
        "Material ID",
        "Price",
    ]
    assert price_df["Price"].map(lambda val: isinstance(val, Decimal)).all()
    assert (price_df["Price"] >= 0).all()


def test_load_pricing_data_missing_column() -> None:
    """Loading a CSV with missing required columns raises a PlanningValidationError."""

    csv_source = StringIO(
        "Sold to ID,Ship to ID,Price\n" "CUST-001,SHIP-001-NL,250.00\n"
    )

    with pytest.raises(PlanningValidationError) as excinfo:
        load_pricing_data(csv_source)

    report = excinfo.value.report
    assert report.is_valid is False
    assert any(issue.column == "Material ID" for issue in report.issues)


def test_load_pricing_data_missing_value() -> None:
    """Loading a CSV with blank fields raises a PlanningValidationError."""

    csv_source = StringIO(
        "Sold to ID,Ship to ID,Material ID,Price\n"
        "CUST-001,SHIP-001-NL,,250.00\n"  # Missing Material ID
    )

    with pytest.raises(PlanningValidationError) as excinfo:
        load_pricing_data(csv_source)

    report = excinfo.value.report
    assert report.is_valid is False
    assert any(
        issue.column == "Material ID"
        and "missing or blank" in issue.message
        for issue in report.issues
    )


def test_load_pricing_data_negative_price() -> None:
    """Loading a CSV with negative price values raises a PlanningValidationError."""

    csv_source = StringIO(
        "Sold to ID,Ship to ID,Material ID,Price\n"
        "CUST-001,SHIP-001-NL,MAT-1001,-15.50\n"
    )

    with pytest.raises(PlanningValidationError) as excinfo:
        load_pricing_data(csv_source)

    report = excinfo.value.report
    assert report.is_valid is False
    assert any("Price cannot be negative" in issue.message for issue in report.issues)


def test_load_pricing_data_non_numeric_price() -> None:
    """Loading a CSV with non-numeric price values raises a PlanningValidationError."""

    csv_source = StringIO(
        "Sold to ID,Ship to ID,Material ID,Price\n"
        "CUST-001,SHIP-001-NL,MAT-1001,abc\n"
    )

    with pytest.raises(PlanningValidationError) as excinfo:
        load_pricing_data(csv_source)

    report = excinfo.value.report
    assert report.is_valid is False
    assert any("valid numeric value" in issue.message for issue in report.issues)


def test_load_pricing_data_duplicate_grain() -> None:
    """Loading a CSV with duplicate combinations of grain raises a PlanningValidationError."""

    csv_source = StringIO(
        "Sold to ID,Ship to ID,Material ID,Price\n"
        "CUST-001,SHIP-001-NL,MAT-1001,250.00\n"
        "CUST-001,SHIP-001-NL,MAT-1001,270.00\n"  # Duplicate combination
    )

    with pytest.raises(PlanningValidationError) as excinfo:
        load_pricing_data(csv_source)

    report = excinfo.value.report
    assert report.is_valid is False
    assert any(
        "Duplicate pricing grain combination" in issue.message
        for issue in report.issues
    )
