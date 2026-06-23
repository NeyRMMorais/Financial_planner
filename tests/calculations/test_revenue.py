"""Unit tests for the revenue calculation engine."""

from __future__ import annotations

from decimal import Decimal
import pandas as pd
import pytest

from src.financial_planner.calculations.revenue import calculate_revenue


@pytest.fixture
def sample_volume_df() -> pd.DataFrame:
    """Fixture supplying a simple volume dataset."""
    records = [
        {
            "Material": "Premium Resin A",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-01", freq="M"),
            "Sold to ID": "CUST-001",
            "Sold to": "Northstar Manufacturing BV",
            "Ship to ID": "SHIP-001-NL",
            "Ship to": "Rotterdam Plant",
            "Plant": "PLANT-01",
            "Volume": Decimal("100.000"),
        },
        {
            "Material": "Premium Resin A",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-02", freq="M"),
            "Sold to ID": "CUST-001",
            "Sold to": "Northstar Manufacturing BV",
            "Ship to ID": "SHIP-001-NL",
            "Ship to": "Rotterdam Plant",
            "Plant": "PLANT-01",
            "Volume": Decimal("150.500"),
        },
        {
            "Material": "Industrial Additive B",
            "Material ID": "MAT-2004",
            "Date": pd.Period("2026-01", freq="M"),
            "Sold to ID": "CUST-002",
            "Sold to": "HelioPack GmbH",
            "Ship to ID": "SHIP-002-DE",
            "Ship to": "Hamburg Site",
            "Plant": "PLANT-02",
            "Volume": Decimal("0.000"),  # Zero volume row
        },
    ]
    return pd.DataFrame(records)


@pytest.fixture
def sample_resolved_prices_df() -> pd.DataFrame:
    """Fixture supplying a simple resolved monthly prices table (in LC)."""
    records = [
        {
            "Sold to ID": "CUST-001",
            "Ship to ID": "SHIP-001-NL",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-01", freq="M"),
            "Price": Decimal("250.00"),
        },
        {
            "Sold to ID": "CUST-001",
            "Ship to ID": "SHIP-001-NL",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-02", freq="M"),
            "Price": Decimal("300.00"),
        },
        {
            "Sold to ID": "CUST-002",
            "Ship to ID": "SHIP-002-DE",
            "Material ID": "MAT-2004",
            "Date": pd.Period("2026-01", freq="M"),
            "Price": Decimal("150.00"),
        },
    ]
    return pd.DataFrame(records)


@pytest.fixture
def sample_plant_currency_df() -> pd.DataFrame:
    """Fixture supplying plant currency mapping."""
    records = [
        {"Plant": "PLANT-01", "Currency": "EUR"},
        {"Plant": "PLANT-02", "Currency": "USD"},
    ]
    return pd.DataFrame(records)


@pytest.fixture
def sample_fx_rates_df() -> pd.DataFrame:
    """Fixture supplying FX rates (units of currency per 1 USD)."""
    records = [
        {"Period": "2026-01", "Currency": "EUR", "Rate": Decimal("0.9000"), "Date": pd.Period("2026-01", freq="M")},
        {"Period": "2026-02", "Currency": "EUR", "Rate": Decimal("0.9200"), "Date": pd.Period("2026-02", freq="M")},
        {"Period": "2026-01", "Currency": "USD", "Rate": Decimal("1.0000"), "Date": pd.Period("2026-01", freq="M")},
        {"Period": "2026-02", "Currency": "USD", "Rate": Decimal("1.0000"), "Date": pd.Period("2026-02", freq="M")},
    ]
    return pd.DataFrame(records)


def test_calculate_revenue_happy_path(
    sample_volume_df: pd.DataFrame,
    sample_resolved_prices_df: pd.DataFrame,
    sample_plant_currency_df: pd.DataFrame,
    sample_fx_rates_df: pd.DataFrame,
) -> None:
    """Verify standard revenue calculations with matching prices."""
    result = calculate_revenue(
        sample_volume_df,
        sample_resolved_prices_df,
        sample_plant_currency_df,
        sample_fx_rates_df,
    )

    assert len(result) == 3
    assert "Price_LC" in result.columns
    assert "Price_USD" in result.columns
    assert "Revenue_LC" in result.columns
    assert "Revenue_USD" in result.columns

    # Check first record: 100 tons, price 250 EUR (LC)
    # EUR rate 0.90. Price USD = 250 / 0.90 = 277.7777...
    # Revenue LC = 100 * 250 = 25000 EUR
    # Revenue USD = 100 * (250/0.90) = 27777.777...
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["Price_LC"] == Decimal("250.00")
    assert abs(r1["Price_USD"] - Decimal("277.7777")) < Decimal("0.001")
    assert r1["Revenue_LC"] == Decimal("25000.00000")
    assert abs(r1["Revenue_USD"] - Decimal("27777.7777")) < Decimal("0.001")

    # Check second record: 150.5 tons, price 300 EUR (LC)
    # EUR rate 0.92. Price USD = 300 / 0.92 = 326.0869...
    # Revenue LC = 150.5 * 300 = 45150 EUR
    # Revenue USD = 150.5 * (300/0.92) = 49076.0869...
    r2 = result.iloc[1]
    assert r2["Volume"] == Decimal("150.500")
    assert r2["Price_LC"] == Decimal("300.00")
    assert abs(r2["Price_USD"] - Decimal("326.0869")) < Decimal("0.001")
    assert r2["Revenue_LC"] == Decimal("45150.00000")
    assert abs(r2["Revenue_USD"] - Decimal("49076.0869")) < Decimal("0.001")


def test_calculate_revenue_missing_price_raises_error(
    sample_volume_df: pd.DataFrame,
    sample_plant_currency_df: pd.DataFrame,
    sample_fx_rates_df: pd.DataFrame,
) -> None:
    """Verify that a ValueError is raised if a volume combination has no matching price."""
    incomplete_prices = pd.DataFrame(
        [
            {
                "Sold to ID": "CUST-001",
                "Ship to ID": "SHIP-001-NL",
                "Material ID": "MAT-1001",
                "Date": pd.Period("2026-01", freq="M"),
                "Price": Decimal("250.00"),
            },
            {
                "Sold to ID": "CUST-001",
                "Ship to ID": "SHIP-001-NL",
                "Material ID": "MAT-1001",
                "Date": pd.Period("2026-02", freq="M"),
                "Price": Decimal("300.00"),
            },
        ]
    )

    with pytest.raises(ValueError) as excinfo:
        calculate_revenue(
            sample_volume_df,
            incomplete_prices,
            sample_plant_currency_df,
            sample_fx_rates_df,
        )

    assert "Missing unit pricing configuration for combinations" in str(
        excinfo.value
    )


def test_calculate_revenue_empty_input(
    sample_plant_currency_df: pd.DataFrame,
    sample_fx_rates_df: pd.DataFrame,
) -> None:
    """Verify that an empty DataFrame is returned when inputs are empty."""
    empty_vol = pd.DataFrame(columns=["Sold to ID", "Ship to ID", "Material ID", "Date", "Volume", "Plant"])
    empty_prices = pd.DataFrame(columns=["Sold to ID", "Ship to ID", "Material ID", "Date", "Price"])

    result = calculate_revenue(
        empty_vol,
        empty_prices,
        sample_plant_currency_df,
        sample_fx_rates_df,
    )
    assert result.empty
    assert "Revenue_LC" in result.columns
    assert "Revenue_USD" in result.columns
    assert "Price_LC" in result.columns
    assert "Price_USD" in result.columns
