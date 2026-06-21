"""Unit tests for monthly raw material cost calculations."""

from __future__ import annotations

from decimal import Decimal
import pandas as pd
import pytest

from src.financial_planner.calculations.costs import calculate_rm_costs


@pytest.fixture
def volume_df() -> pd.DataFrame:
    """Fixture supplying a simple volume dataset."""
    records = [
        {
            "Plant": "PLANT-01",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-01", freq="M"),
            "Volume": Decimal("100.000"),
        },
        {
            "Plant": "PLANT-01",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-02", freq="M"),
            "Volume": Decimal("150.500"),
        },
        {
            "Plant": "PLANT-02",
            "Material ID": "MAT-2004",
            "Date": pd.Period("2026-01", freq="M"),
            "Volume": Decimal("0.000"),  # Zero volume row
        },
    ]
    return pd.DataFrame(records)


@pytest.fixture
def cost_df() -> pd.DataFrame:
    """Fixture supplying a simple cost dataset."""
    records = [
        {
            "Plant": "PLANT-01",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-01", freq="M"),
            "Cost": Decimal("120.00"),
        },
        {
            "Plant": "PLANT-01",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-02", freq="M"),
            "Cost": Decimal("125.50"),
        },
        {
            "Plant": "PLANT-02",
            "Material ID": "MAT-2004",
            "Date": pd.Period("2026-01", freq="M"),
            "Cost": Decimal("80.00"),
        },
    ]
    return pd.DataFrame(records)


def test_calculate_rm_costs_happy_path(
    volume_df: pd.DataFrame,
    cost_df: pd.DataFrame,
) -> None:
    """Verify standard raw material cost calculations."""
    result = calculate_rm_costs(volume_df, cost_df)

    assert len(result) == 3
    assert "Cost" in result.columns
    assert "Total RM Cost" in result.columns

    # Check PLANT-01, MAT-1001, 2026-01: 100 tons * $120.00 = $12,000.00
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["Cost"] == Decimal("120.00")
    assert r1["Total RM Cost"] == Decimal("12000.00000")

    # Check PLANT-01, MAT-1001, 2026-02: 150.5 tons * $125.50 = $18,887.75
    r2 = result.iloc[1]
    assert r2["Volume"] == Decimal("150.500")
    assert r2["Cost"] == Decimal("125.50")
    assert r2["Total RM Cost"] == Decimal("18887.75000")

    # Check PLANT-02, MAT-2004, 2026-01: 0 tons * $80.00 = $0.00
    r3 = result.iloc[2]
    assert r3["Volume"] == Decimal("0.000")
    assert r3["Cost"] == Decimal("80.00")
    assert r3["Total RM Cost"] == Decimal("0.0000")


def test_calculate_rm_costs_missing_costs_raises_error(
    volume_df: pd.DataFrame,
) -> None:
    """Verify that a ValueError is raised if a volume combination lacks cost configuration."""
    # Cost table missing PLANT-02, MAT-2004 cost
    incomplete_costs = pd.DataFrame(
        [
            {
                "Plant": "PLANT-01",
                "Material ID": "MAT-1001",
                "Date": pd.Period("2026-01", freq="M"),
                "Cost": Decimal("120.00"),
            },
            {
                "Plant": "PLANT-01",
                "Material ID": "MAT-1001",
                "Date": pd.Period("2026-02", freq="M"),
                "Cost": Decimal("125.50"),
            },
        ]
    )

    with pytest.raises(ValueError) as excinfo:
        calculate_rm_costs(volume_df, incomplete_costs)

    assert "Missing raw material unit costs for combinations" in str(
        excinfo.value
    )


def test_calculate_rm_costs_empty_input() -> None:
    """Verify that empty inputs result in an empty DataFrame with the correct schema."""
    empty_vol = pd.DataFrame(columns=["Plant", "Material ID", "Date", "Volume"])
    empty_costs = pd.DataFrame(columns=["Plant", "Material ID", "Date", "Cost"])

    result = calculate_rm_costs(empty_vol, empty_costs)
    assert result.empty
    assert "Total RM Cost" in result.columns
    assert "Cost" in result.columns


@pytest.fixture
def var_cost_df() -> pd.DataFrame:
    """Fixture supplying a simple annual variable cost dataset."""
    records = [
        {
            "Material": "Poly A",
            "Material ID": "MAT-1001",
            "Variable Cost": Decimal("15.50"),
        },
        {
            "Material": "Resin B",
            "Material ID": "MAT-2004",
            "Variable Cost": Decimal("22.00"),
        },
    ]
    return pd.DataFrame(records)


def test_calculate_variable_costs_happy_path(
    volume_df: pd.DataFrame,
    var_cost_df: pd.DataFrame,
) -> None:
    """Verify standard variable cost calculations."""
    from src.financial_planner.calculations.costs import calculate_variable_costs

    result = calculate_variable_costs(volume_df, var_cost_df)

    assert len(result) == 3
    assert "Variable Cost" in result.columns
    assert "Total Variable Cost" in result.columns

    # Check MAT-1001, 2026-01: 100 tons * $15.50 = $1,550.00
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["Variable Cost"] == Decimal("15.50")
    assert r1["Total Variable Cost"] == Decimal("1550.00000")

    # Check MAT-1001, 2026-02: 150.5 tons * $15.50 = $2,332.75
    r2 = result.iloc[1]
    assert r2["Volume"] == Decimal("150.500")
    assert r2["Variable Cost"] == Decimal("15.50")
    assert r2["Total Variable Cost"] == Decimal("2332.75000")

    # Check MAT-2004, 2026-01: 0 tons * $22.00 = $0.00
    r3 = result.iloc[2]
    assert r3["Volume"] == Decimal("0.000")
    assert r3["Variable Cost"] == Decimal("22.00")
    assert r3["Total Variable Cost"] == Decimal("0.0000")


def test_calculate_variable_costs_missing_raises_error(
    volume_df: pd.DataFrame,
) -> None:
    """Verify missing variable costs raise an error."""
    from src.financial_planner.calculations.costs import calculate_variable_costs

    incomplete_costs = pd.DataFrame(
        [
            {
                "Material": "Poly A",
                "Material ID": "MAT-1001",
                "Variable Cost": Decimal("15.50"),
            }
        ]
    )

    with pytest.raises(ValueError) as excinfo:
        calculate_variable_costs(volume_df, incomplete_costs)

    assert "Missing variable costs for materials" in str(excinfo.value)
