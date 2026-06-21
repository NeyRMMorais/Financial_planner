"""Unit tests for the pricing override propagation calculations."""

from __future__ import annotations

from decimal import Decimal
import pandas as pd
import pytest

from src.financial_planner.calculations.pricing import (
    PriceOverride,
    resolve_monthly_prices,
)


@pytest.fixture
def base_prices_df() -> pd.DataFrame:
    """Fixture supplying a simple base prices table."""

    records = [
        {
            "Sold to ID": "CUST-001",
            "Ship to ID": "SHIP-001-NL",
            "Material ID": "MAT-1001",
            "Price": Decimal("200.00"),
        },
        {
            "Sold to ID": "CUST-002",
            "Ship to ID": "SHIP-002-DE",
            "Material ID": "MAT-2004",
            "Price": Decimal("350.00"),
        },
    ]
    return pd.DataFrame(records)


def test_resolve_monthly_prices_no_overrides(
    base_prices_df: pd.DataFrame,
) -> None:
    """Without overrides, base prices apply constantly to all 12 periods of 2026."""

    resolved = resolve_monthly_prices(base_prices_df, [])

    # We expect 2 combinations * 12 months = 24 rows
    assert len(resolved) == 24
    assert list(resolved.columns) == [
        "Sold to ID",
        "Ship to ID",
        "Material ID",
        "Date",
        "Price",
    ]

    # Verify CUST-001 prices are all 200.00
    cust1 = resolved[resolved["Sold to ID"] == "CUST-001"]
    assert len(cust1) == 12
    assert (cust1["Price"] == Decimal("200.00")).all()
    # Check periods
    expected_months = [pd.Period(f"2026-{m:02d}", freq="M") for m in range(1, 13)]
    assert list(cust1["Date"]) == expected_months


def test_resolve_monthly_prices_single_override(
    base_prices_df: pd.DataFrame,
) -> None:
    """A single override starting mid-year replaces prices from that month forward."""

    overrides = [
        PriceOverride(
            material_id="MAT-1001",
            sold_to_id="CUST-001",
            ship_to_id="SHIP-001-NL",
            start_month=pd.Period("2026-06", freq="M"),
            new_price=Decimal("250.00"),
        )
    ]

    resolved = resolve_monthly_prices(base_prices_df, overrides)

    cust1 = resolved[resolved["Sold to ID"] == "CUST-001"].sort_values("Date")
    assert len(cust1) == 12

    # Months 1-5 (Jan to May) should be base price 200.00
    for month in range(1, 6):
        period = pd.Period(f"2026-{month:02d}", freq="M")
        row = cust1[cust1["Date"] == period]
        assert row["Price"].values[0] == Decimal("200.00")

    # Months 6-12 (Jun to Dec) should be overridden price 250.00
    for month in range(6, 13):
        period = pd.Period(f"2026-{month:02d}", freq="M")
        row = cust1[cust1["Date"] == period]
        assert row["Price"].values[0] == Decimal("250.00")

    # Verify that CUST-002 remains unaffected at 350.00
    cust2 = resolved[resolved["Sold to ID"] == "CUST-002"]
    assert (cust2["Price"] == Decimal("350.00")).all()


def test_resolve_monthly_prices_multiple_overrides(
    base_prices_df: pd.DataFrame,
) -> None:
    """Multiple sequential overrides replace values forward in steps."""

    overrides = [
        PriceOverride(
            material_id="MAT-1001",
            sold_to_id="CUST-001",
            ship_to_id="SHIP-001-NL",
            start_month=pd.Period("2026-04", freq="M"),
            new_price=Decimal("220.00"),
        ),
        PriceOverride(
            material_id="MAT-1001",
            sold_to_id="CUST-001",
            ship_to_id="SHIP-001-NL",
            start_month=pd.Period("2026-09", freq="M"),
            new_price=Decimal("280.00"),
        ),
    ]

    resolved = resolve_monthly_prices(base_prices_df, overrides)

    cust1 = resolved[resolved["Sold to ID"] == "CUST-001"].sort_values("Date")

    # Jan - Mar (1-3): 200.00
    for month in range(1, 4):
        period = pd.Period(f"2026-{month:02d}", freq="M")
        assert cust1[cust1["Date"] == period]["Price"].values[0] == Decimal(
            "200.00"
        )

    # Apr - Aug (4-8): 220.00
    for month in range(4, 9):
        period = pd.Period(f"2026-{month:02d}", freq="M")
        assert cust1[cust1["Date"] == period]["Price"].values[0] == Decimal(
            "220.00"
        )

    # Sep - Dec (9-12): 280.00
    for month in range(9, 13):
        period = pd.Period(f"2026-{month:02d}", freq="M")
        assert cust1[cust1["Date"] == period]["Price"].values[0] == Decimal(
            "280.00"
        )
