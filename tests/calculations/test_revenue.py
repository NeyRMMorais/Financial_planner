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
            "Volume": Decimal("0.000"),  # Zero volume row
        },
    ]
    return pd.DataFrame(records)


@pytest.fixture
def sample_resolved_prices_df() -> pd.DataFrame:
    """Fixture supplying a simple resolved monthly prices table."""
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


def test_calculate_revenue_happy_path(
    sample_volume_df: pd.DataFrame,
    sample_resolved_prices_df: pd.DataFrame,
) -> None:
    """Verify standard revenue calculations with matching prices."""
    result = calculate_revenue(sample_volume_df, sample_resolved_prices_df)

    assert len(result) == 3
    assert "Price" in result.columns
    assert "Revenue" in result.columns

    # Check first record: 100 tons * $250.00 = $25,000.00
    r1 = result.iloc[0]
    assert r1["Volume"] == Decimal("100.000")
    assert r1["Price"] == Decimal("250.00")
    assert r1["Revenue"] == Decimal("25000.00000")

    # Check second record: 150.5 tons * $300.00 = $45,150.00
    r2 = result.iloc[1]
    assert r2["Volume"] == Decimal("150.500")
    assert r2["Price"] == Decimal("300.00")
    assert r2["Revenue"] == Decimal("45150.00000")

    # Check third record: 0 tons * $150.00 = $0.00
    r3 = result.iloc[2]
    assert r3["Volume"] == Decimal("0.000")
    assert r3["Price"] == Decimal("150.00")
    assert r3["Revenue"] == Decimal("0.0000")


def test_calculate_revenue_missing_price_raises_error(
    sample_volume_df: pd.DataFrame,
) -> None:
    """Verify that a ValueError is raised if a volume combination has no matching price."""
    # Prices table missing MAT-2004 price
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
        calculate_revenue(sample_volume_df, incomplete_prices)

    assert "Missing unit pricing configuration for combinations" in str(
        excinfo.value
    )


def test_calculate_revenue_empty_input() -> None:
    """Verify that an empty DataFrame is returned when inputs are empty."""
    empty_vol = pd.DataFrame(columns=["Sold to ID", "Ship to ID", "Material ID", "Date", "Volume"])
    empty_prices = pd.DataFrame(columns=["Sold to ID", "Ship to ID", "Material ID", "Date", "Price"])

    result = calculate_revenue(empty_vol, empty_prices)
    assert result.empty
    assert "Revenue" in result.columns
    assert "Price" in result.columns
