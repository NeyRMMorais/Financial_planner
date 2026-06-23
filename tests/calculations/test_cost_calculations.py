"""Unit tests for monthly raw material, variable, and distribution cost calculations with FX."""

from __future__ import annotations

from decimal import Decimal
import pandas as pd
import pytest

from src.financial_planner.calculations.costs import (
    calculate_rm_costs,
    calculate_variable_costs,
    calculate_distribution_costs,
)


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
    """Fixture supplying a simple RM cost dataset in EUR."""
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


@pytest.fixture
def plant_currency_df() -> pd.DataFrame:
    """Fixture supplying plant currency mappings."""
    records = [
        {"Plant": "PLANT-01", "Currency": "EUR"},
        {"Plant": "PLANT-02", "Currency": "USD"},
    ]
    return pd.DataFrame(records)


@pytest.fixture
def fx_rates_df() -> pd.DataFrame:
    """Fixture supplying monthly FX rates (units of currency per 1 USD)."""
    records = [
        {"Period": "2026-01", "Currency": "EUR", "Rate": Decimal("0.9000"), "Date": pd.Period("2026-01", freq="M")},
        {"Period": "2026-02", "Currency": "EUR", "Rate": Decimal("0.9200"), "Date": pd.Period("2026-02", freq="M")},
        {"Period": "2026-01", "Currency": "USD", "Rate": Decimal("1.0000"), "Date": pd.Period("2026-01", freq="M")},
        {"Period": "2026-02", "Currency": "USD", "Rate": Decimal("1.0000"), "Date": pd.Period("2026-02", freq="M")},
    ]
    return pd.DataFrame(records)


def test_calculate_rm_costs_happy_path(
    volume_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify standard raw material cost calculations."""
    result = calculate_rm_costs(volume_df, cost_df, plant_currency_df, fx_rates_df)

    assert len(result) == 3
    assert "RM_Cost_EUR" in result.columns
    assert "RM_Cost_USD" in result.columns
    assert "RM_Cost_LC" in result.columns
    assert "Total_RM_Cost_USD" in result.columns
    assert "Total_RM_Cost_LC" in result.columns

    # PLANT-01 (EUR), MAT-1001, 2026-01: 100 tons, cost 120.00 EUR
    # EUR rate 0.90. RM_Cost_USD = 120 / 0.90 = 133.3333
    # RM_Cost_LC = 133.3333 * 0.90 = 120.00 EUR
    # Total USD = 100 * 133.3333 = 13333.333...
    # Total LC = 100 * 120 = 12000.00
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["RM_Cost_EUR"] == Decimal("120.00")
    assert abs(r1["RM_Cost_USD"] - Decimal("133.3333")) < Decimal("0.001")
    assert r1["RM_Cost_LC"] == Decimal("120.00")
    assert abs(r1["Total_RM_Cost_USD"] - Decimal("13333.3333")) < Decimal("0.001")
    assert r1["Total_RM_Cost_LC"] == Decimal("12000.0000")


def test_calculate_rm_costs_missing_costs_raises_error(
    volume_df: pd.DataFrame,
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify that a ValueError is raised if a volume combination lacks cost configuration."""
    incomplete_costs = pd.DataFrame(
        [
            {
                "Plant": "PLANT-01",
                "Material ID": "MAT-1001",
                "Date": pd.Period("2026-01", freq="M"),
                "Cost": Decimal("120.00"),
            },
        ]
    )

    with pytest.raises(ValueError):
        calculate_rm_costs(volume_df, incomplete_costs, plant_currency_df, fx_rates_df)


def test_calculate_rm_costs_empty_input(
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify that empty inputs result in an empty DataFrame with the correct schema."""
    empty_vol = pd.DataFrame(columns=["Plant", "Material ID", "Date", "Volume"])
    empty_costs = pd.DataFrame(columns=["Plant", "Material ID", "Date", "Cost"])

    result = calculate_rm_costs(empty_vol, empty_costs, plant_currency_df, fx_rates_df)
    assert result.empty
    assert "RM_Cost_EUR" in result.columns
    assert "RM_Cost_USD" in result.columns
    assert "RM_Cost_LC" in result.columns
    assert "Total_RM_Cost_USD" in result.columns
    assert "Total_RM_Cost_LC" in result.columns


@pytest.fixture
def var_cost_df() -> pd.DataFrame:
    """Fixture supplying a simple annual variable cost dataset in EUR."""
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
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify standard variable cost calculations."""
    result = calculate_variable_costs(volume_df, var_cost_df, plant_currency_df, fx_rates_df)

    assert len(result) == 3
    assert "Var_Cost_EUR" in result.columns
    assert "Var_Cost_USD" in result.columns
    assert "Var_Cost_LC" in result.columns
    assert "Total_Variable_Cost_USD" in result.columns
    assert "Total_Variable_Cost_LC" in result.columns

    # Check PLANT-01 (EUR), MAT-1001, 2026-01: 100 tons, cost 15.50 EUR
    # EUR rate 0.90. Var_Cost_USD = 15.50 / 0.90 = 17.2222
    # Var_Cost_LC = 15.50 EUR
    # Total USD = 1722.22...
    # Total LC = 1550.00
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["Var_Cost_EUR"] == Decimal("15.50")
    assert abs(r1["Var_Cost_USD"] - Decimal("17.2222")) < Decimal("0.001")
    assert r1["Var_Cost_LC"] == Decimal("15.50")
    assert abs(r1["Total_Variable_Cost_USD"] - Decimal("1722.2222")) < Decimal("0.001")
    assert r1["Total_Variable_Cost_LC"] == Decimal("1550.00")


def test_calculate_variable_costs_missing_raises_error(
    volume_df: pd.DataFrame,
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify missing variable costs raise an error."""
    incomplete_costs = pd.DataFrame(
        [
            {
                "Material": "Poly A",
                "Material ID": "MAT-1001",
                "Variable Cost": Decimal("15.50"),
            }
        ]
    )

    with pytest.raises(ValueError):
        calculate_variable_costs(volume_df, incomplete_costs, plant_currency_df, fx_rates_df)


@pytest.fixture
def dist_cost_df() -> pd.DataFrame:
    """Fixture supplying a simple annual distribution cost dataset in LC."""
    records = [
        {
            "Ship to": "Location A",
            "Ship to ID": "SHIP-001",
            "Distribution Cost": Decimal("10.00"),
        },
        {
            "Ship to": "Location B",
            "Ship to ID": "SHIP-002",
            "Distribution Cost": Decimal("25.00"),
        },
    ]
    return pd.DataFrame(records)


def test_calculate_distribution_costs_happy_path(
    dist_cost_df: pd.DataFrame,
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify standard distribution cost calculations."""
    volume_df = pd.DataFrame([
        {
            "Ship to ID": "SHIP-001",
            "Volume": Decimal("100.000"),
            "Plant": "PLANT-01",
            "Date": pd.Period("2026-01", freq="M"),
        },
        {
            "Ship to ID": "SHIP-001",
            "Volume": Decimal("50.000"),
            "Plant": "PLANT-01",
            "Date": pd.Period("2026-02", freq="M"),
        },
        {
            "Ship to ID": "SHIP-002",
            "Volume": Decimal("0.000"),
            "Plant": "PLANT-02",
            "Date": pd.Period("2026-01", freq="M"),
        },
    ])

    result = calculate_distribution_costs(volume_df, dist_cost_df, plant_currency_df, fx_rates_df)

    assert len(result) == 3
    assert "Dist_Cost_LC" in result.columns
    assert "Dist_Cost_USD" in result.columns
    assert "Total_Distribution_Cost_USD" in result.columns
    assert "Total_Distribution_Cost_LC" in result.columns

    # Ship to SHIP-001, PLANT-01 (EUR), 2026-01: 100 tons, cost 10.00 EUR (LC)
    # EUR rate 0.90. Dist_Cost_USD = 10 / 0.90 = 11.1111
    # Total USD = 1111.111...
    # Total LC = 1000.00
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["Dist_Cost_LC"] == Decimal("10.00")
    assert abs(r1["Dist_Cost_USD"] - Decimal("11.1111")) < Decimal("0.001")
    assert abs(r1["Total_Distribution_Cost_USD"] - Decimal("1111.1111")) < Decimal("0.001")
    assert r1["Total_Distribution_Cost_LC"] == Decimal("1000.00")


def test_calculate_distribution_costs_missing_raises_error(
    plant_currency_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> None:
    """Verify missing distribution costs raise an error."""
    volume_df = pd.DataFrame([
        {
            "Ship to ID": "SHIP-001",
            "Volume": Decimal("100.000"),
            "Plant": "PLANT-01",
            "Date": pd.Period("2026-01", freq="M"),
        },
    ])

    incomplete_costs = pd.DataFrame(
        [
            {
                "Ship to": "Location B",
                "Ship to ID": "SHIP-002",
                "Distribution Cost": Decimal("25.00"),
            }
        ]
    )

    with pytest.raises(ValueError):
        calculate_distribution_costs(volume_df, incomplete_costs, plant_currency_df, fx_rates_df)
