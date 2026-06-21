"""Unit tests for monthly raw material cost ingestion and validation."""

from __future__ import annotations

from decimal import Decimal
from io import StringIO
import pandas as pd
import pytest

from src.financial_planner.data_ingestion.cost_loader import load_cost_data
from src.financial_planner.data_ingestion.validation import (
    PlanningValidationError,
    run_cost_validation,
    validate_cost_completeness,
)


def test_load_cost_data_success() -> None:
    """Verify that a valid cost CSV file is successfully ingested and formatted."""
    csv_content = (
        "Plant,Material ID,Period,Cost\n"
        "PLANT-01,MAT-1001,2026-01,150.00\n"
        "PLANT-01,MAT-1001,2026-02,152.50\n"
        "PLANT-02,MAT-2004,2026-01,180.00\n"
    )
    df = load_cost_data(StringIO(csv_content))

    assert len(df) == 3
    assert list(df.columns) == ["Plant", "Material ID", "Period", "Cost", "Date"]
    assert df.loc[0, "Date"] == pd.Period("2026-01", freq="M")
    assert df.loc[0, "Cost"] == Decimal("150.00")
    assert df.loc[2, "Cost"] == Decimal("180.00")


def test_load_cost_data_validation_errors() -> None:
    """Verify that invalid cost records trigger PlanningValidationError."""
    # Test negative cost
    csv_negative = (
        "Plant,Material ID,Period,Cost\n"
        "PLANT-01,MAT-1001,2026-01,-150.00\n"
    )
    with pytest.raises(PlanningValidationError):
        load_cost_data(StringIO(csv_negative))

    # Test invalid period format
    csv_period = (
        "Plant,Material ID,Period,Cost\n"
        "PLANT-01,MAT-1001,2026/01,150.00\n"
    )
    with pytest.raises(PlanningValidationError):
        load_cost_data(StringIO(csv_period))

    # Test duplicates
    csv_duplicate = (
        "Plant,Material ID,Period,Cost\n"
        "PLANT-01,MAT-1001,2026-01,150.00\n"
        "PLANT-01,MAT-1001,2026-01,160.00\n"
    )
    with pytest.raises(PlanningValidationError):
        load_cost_data(StringIO(csv_duplicate))


def test_validate_cost_completeness_reconciliation() -> None:
    """Verify that missing cost configurations are flagged as completeness errors."""
    volume_df = pd.DataFrame(
        [
            {
                "Plant": "PLANT-01",
                "Material ID": "MAT-1001",
                "Date": pd.Period("2026-01", freq="M"),
            },
            {
                "Plant": "PLANT-02",
                "Material ID": "MAT-2004",
                "Date": pd.Period("2026-01", freq="M"),
            },
        ]
    )

    # Cost df missing PLANT-02, MAT-2004, 2026-01
    cost_df = pd.DataFrame(
        [
            {
                "Plant": "PLANT-01",
                "Material ID": "MAT-1001",
                "Period": "2026-01",
                "Cost": Decimal("150.00"),
            }
        ]
    )

    issues = validate_cost_completeness(volume_df, cost_df)
    assert len(issues) == 1
    assert issues[0].column == "Cost"
    assert "PLANT-02" in issues[0].value
    assert "MAT-2004" in issues[0].value
    assert "2026-01" in issues[0].value
