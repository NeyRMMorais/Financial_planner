"""Unit tests for the advanced validation module."""

from __future__ import annotations

from decimal import Decimal
import pandas as pd
import pytest

from src.financial_planner.data_ingestion.validation import (
    PLANNING_VOLUME_COLUMNS,
    run_advanced_validation,
    validate_dates_format_and_range,
    validate_grain_uniqueness,
    validate_nulls_and_empty,
    validate_schema,
    validate_volumes_format_and_sign,
)


@pytest.fixture
def valid_record_df() -> pd.DataFrame:
    """Fixture supplying a single valid planning volume record as a DataFrame."""

    record = {
        "Material": "Premium Resin A",
        "Material ID": "MAT-1001",
        "Date": "2026-01",
        "Sold to ID": "CUST-001",
        "Sold to": "Northstar Manufacturing BV",
        "Ship to ID": "SHIP-001-NL",
        "Ship to": "Northstar Manufacturing BV - Rotterdam Plant",
        "Volume": "125.500",
    }
    return pd.DataFrame([record])


def test_validate_schema_success(valid_record_df: pd.DataFrame) -> None:
    """A DataFrame containing all required columns has no schema issues."""

    issues = validate_schema(valid_record_df)
    assert len(issues) == 0


def test_validate_schema_missing_column(valid_record_df: pd.DataFrame) -> None:
    """A missing required column creates a schema issue with error severity."""

    df = valid_record_df.drop(columns=["Volume"])
    issues = validate_schema(df)

    assert len(issues) == 1
    assert issues[0].column == "Volume"
    assert issues[0].severity == "error"
    assert "Missing required column" in issues[0].message


def test_validate_nulls_and_empty_success(valid_record_df: pd.DataFrame) -> None:
    """A fully populated valid DataFrame has no null/empty issues."""

    issues = validate_nulls_and_empty(valid_record_df)
    assert len(issues) == 0


def test_validate_nulls_and_empty_blank_and_nan(valid_record_df: pd.DataFrame) -> None:
    """Null and empty values are caught as critical errors with correct row index."""

    df = pd.DataFrame(
        [
            # Row 1: Nan value
            {**valid_record_df.iloc[0].to_dict(), "Material ID": pd.NA},
            # Row 2: Empty string
            {**valid_record_df.iloc[0].to_dict(), "Sold to": "   "},
        ]
    )

    issues = validate_nulls_and_empty(df)

    assert len(issues) == 2
    # Row 1 check
    assert issues[0].column == "Material ID"
    assert issues[0].row_index == 1
    assert issues[0].severity == "error"

    # Row 2 check
    assert issues[1].column == "Sold to"
    assert issues[1].row_index == 2
    assert issues[1].severity == "error"


def test_validate_dates_success(valid_record_df: pd.DataFrame) -> None:
    """Valid YYYY-MM dates in the 2026 year are accepted."""

    issues = validate_dates_format_and_range(valid_record_df)
    assert len(issues) == 0


def test_validate_dates_invalid_format(valid_record_df: pd.DataFrame) -> None:
    """Incorrectly formatted dates (not YYYY-MM) are flagged as errors."""

    df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026/01"},
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026-1-1"},
            {**valid_record_df.iloc[0].to_dict(), "Date": "Jan 2026"},
        ]
    )

    issues = validate_dates_format_and_range(df)

    assert len(issues) == 3
    for issue in issues:
        assert issue.column == "Date"
        assert issue.severity == "error"
        assert "YYYY-MM format" in issue.message


def test_validate_dates_outside_horizon(valid_record_df: pd.DataFrame) -> None:
    """Dates outside the 2026 calendar year are flagged as errors."""

    df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Date": "2025-12"},
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026-13"},  # Invalid month
            {**valid_record_df.iloc[0].to_dict(), "Date": "2027-01"},
        ]
    )

    issues = validate_dates_format_and_range(df)

    assert len(issues) == 3
    assert "must be exactly 2026" in issues[0].message
    assert "must be between 01 and 12" in issues[1].message
    assert "must be exactly 2026" in issues[2].message


def test_validate_volumes_success(valid_record_df: pd.DataFrame) -> None:
    """Volumes that parse to non-negative decimals are accepted."""

    # Test parseable decimal string
    issues = validate_volumes_format_and_sign(valid_record_df)
    assert len(issues) == 0

    # Test actual Decimal object
    df = valid_record_df.copy()
    df["Volume"] = df["Volume"].astype(object)
    df.loc[0, "Volume"] = Decimal("5.123")
    issues = validate_volumes_format_and_sign(df)
    assert len(issues) == 0


def test_validate_volumes_negative(valid_record_df: pd.DataFrame) -> None:
    """Negative volume strings and Decimal objects are flagged as errors."""

    df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Volume": "-12.500"},
            {**valid_record_df.iloc[0].to_dict(), "Volume": Decimal("-0.001")},
        ]
    )

    issues = validate_volumes_format_and_sign(df)

    assert len(issues) == 2
    for issue in issues:
        assert issue.column == "Volume"
        assert issue.severity == "error"
        assert "cannot be negative" in issue.message


def test_validate_volumes_non_numeric(valid_record_df: pd.DataFrame) -> None:
    """Non-numeric volume values are flagged as errors."""

    df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Volume": "abc"},
            {**valid_record_df.iloc[0].to_dict(), "Volume": "12.3.4"},
        ]
    )

    issues = validate_volumes_format_and_sign(df)

    assert len(issues) == 2
    for issue in issues:
        assert issue.column == "Volume"
        assert issue.severity == "error"
        assert "valid numeric value" in issue.message


def test_validate_grain_uniqueness_success(valid_record_df: pd.DataFrame) -> None:
    """Distinct grain rows do not trigger duplicate warnings."""

    df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026-01"},
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026-02"},
        ]
    )

    issues = validate_grain_uniqueness(df)
    assert len(issues) == 0


def test_validate_grain_uniqueness_duplicate(valid_record_df: pd.DataFrame) -> None:
    """Duplicate grain rows trigger validation warnings rather than blocking errors."""

    df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026-01", "Volume": "10"},
            {**valid_record_df.iloc[0].to_dict(), "Date": "2026-01", "Volume": "20"},
        ]
    )

    issues = validate_grain_uniqueness(df)

    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "Duplicate grain combination" in issues[0].message


def test_run_advanced_validation_full_suite(valid_record_df: pd.DataFrame) -> None:
    """Verify combined validation runs correctly and produces correct is_valid flag."""

    # 1. Happy path
    report = run_advanced_validation(valid_record_df)
    assert report.is_valid is True
    assert len(report.issues) == 0

    # 2. Warning path (duplicate grain only)
    warning_df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Volume": "10"},
            {**valid_record_df.iloc[0].to_dict(), "Volume": "20"},
        ]
    )
    report = run_advanced_validation(warning_df)
    assert report.is_valid is True  # Valid because warnings are non-blocking
    assert len(report.issues) == 1
    assert report.issues[0].severity == "warning"

    # 3. Critical error path
    error_df = pd.DataFrame(
        [
            {**valid_record_df.iloc[0].to_dict(), "Volume": "-5"},
        ]
    )
    report = run_advanced_validation(error_df)
    assert report.is_valid is False
    assert len(report.issues) == 1
    assert report.issues[0].severity == "error"
