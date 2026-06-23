"""Unit tests for monthly FX rate and plant currency mapping ingestion and validation."""

from __future__ import annotations

from decimal import Decimal
from io import StringIO
import pandas as pd
import pytest

from src.financial_planner.data_ingestion.fx_loader import (
    load_fx_data,
    load_plant_currency_data,
)
from src.financial_planner.data_ingestion.validation import (
    PlanningValidationError,
    validate_fx_completeness,
)


def test_load_fx_data_success() -> None:
    """Verify that a valid FX rates CSV file is successfully ingested and formatted."""
    csv_content = (
        "Period,Currency,Rate\n"
        "2026-01,EUR,0.9200\n"
        "2026-01,CAD,1.3500\n"
        "2026-02,EUR,0.9150\n"
    )
    df = load_fx_data(StringIO(csv_content))

    assert len(df) == 3
    assert list(df.columns) == ["Period", "Currency", "Rate", "Date"]
    assert df.loc[0, "Date"] == pd.Period("2026-01", freq="M")
    assert df.loc[0, "Currency"] == "EUR"
    assert df.loc[0, "Rate"] == Decimal("0.9200")
    assert df.loc[1, "Rate"] == Decimal("1.3500")


def test_load_fx_data_validation_errors() -> None:
    """Verify that invalid FX records trigger PlanningValidationError."""
    # Test negative/zero rate
    csv_negative = (
        "Period,Currency,Rate\n"
        "2026-01,EUR,-0.9200\n"
    )
    with pytest.raises(PlanningValidationError):
        load_fx_data(StringIO(csv_negative))

    # Test invalid period format
    csv_period = (
        "Period,Currency,Rate\n"
        "2026/01,EUR,0.9200\n"
    )
    with pytest.raises(PlanningValidationError):
        load_fx_data(StringIO(csv_period))

    # Test duplicates (same Period and Currency)
    csv_duplicate = (
        "Period,Currency,Rate\n"
        "2026-01,EUR,0.9200\n"
        "2026-01,EUR,0.9300\n"
    )
    with pytest.raises(PlanningValidationError):
        load_fx_data(StringIO(csv_duplicate))


def test_load_plant_currency_success() -> None:
    """Verify that a valid Plant-Currency mapping CSV file is successfully ingested."""
    csv_content = (
        "Plant,Currency\n"
        "PLANT-01,EUR\n"
        "PLANT-02,CAD\n"
        "PLANT-03,USD\n"
    )
    df = load_plant_currency_data(StringIO(csv_content))

    assert len(df) == 3
    assert list(df.columns) == ["Plant", "Currency"]
    assert df.loc[0, "Plant"] == "PLANT-01"
    assert df.loc[0, "Currency"] == "EUR"


def test_load_plant_currency_validation_errors() -> None:
    """Verify that invalid Plant-Currency mapping records trigger PlanningValidationError."""
    # Test empty fields
    csv_empty = (
        "Plant,Currency\n"
        ",EUR\n"
    )
    with pytest.raises(PlanningValidationError):
        load_plant_currency_data(StringIO(csv_empty))

    # Test duplicate plant mappings
    csv_duplicate = (
        "Plant,Currency\n"
        "PLANT-01,EUR\n"
        "PLANT-01,CAD\n"
    )
    with pytest.raises(PlanningValidationError):
        load_plant_currency_data(StringIO(csv_duplicate))


def test_validate_fx_completeness_reconciliation() -> None:
    """Verify that missing plant mappings or exchange rates are flagged as completeness issues."""
    volume_df = pd.DataFrame(
        [
            {
                "Plant": "PLANT-01",
                "Date": pd.Period("2026-01", freq="M"),
            },
            {
                "Plant": "PLANT-02",
                "Date": pd.Period("2026-01", freq="M"),
            },
        ]
    )

    # 1. Missing PLANT-02 currency mapping
    plant_currency_df = pd.DataFrame([{"Plant": "PLANT-01", "Currency": "EUR"}])
    fx_rates_df = pd.DataFrame(
        [
            {"Period": "2026-01", "Currency": "EUR"},
        ]
    )
    issues = validate_fx_completeness(volume_df, fx_rates_df, plant_currency_df)
    assert len(issues) >= 1
    assert any("PLANT-02" in issue.value for issue in issues)

    # 2. Missing FX rate for PLANT-01 local currency (EUR)
    plant_currency_df_2 = pd.DataFrame(
        [
            {"Plant": "PLANT-01", "Currency": "EUR"},
            {"Plant": "PLANT-02", "Currency": "USD"},
        ]
    )
    fx_rates_df_missing_eur = pd.DataFrame(
        [
            {"Period": "2026-01", "Currency": "CAD"},  # EUR rate is missing
        ]
    )
    issues_2 = validate_fx_completeness(
        volume_df, fx_rates_df_missing_eur, plant_currency_df_2
    )
    assert len(issues_2) >= 1
    assert any("EUR" in issue.value for issue in issues_2)
