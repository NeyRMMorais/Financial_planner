"""Pricing calculation engine.

This module defines structures and functions for resolving monthly planning
prices based on base prices and step-change overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pandas as pd


@dataclass
class PriceOverride:
    """Represents a price override starting from a specific month onward."""

    material_id: str
    sold_to_id: str
    ship_to_id: str
    start_month: pd.Period
    new_price: Decimal


def resolve_monthly_prices(
    base_prices: pd.DataFrame,
    overrides: list[PriceOverride],
    planning_year: int = 2026,
) -> pd.DataFrame:
    """Resolve the final monthly price table for all planning combinations.

    Business rule:
        Base prices are constant for the entire planning year. If a user defines
        an override for a specific month, that override replaces the base price
        for that month and all subsequent months (propagates forward) until
        another later override is encountered.

    Args:
        base_prices: A DataFrame with columns ['Sold to ID', 'Ship to ID', 'Material ID', 'Price'].
        overrides: A list of PriceOverride objects.
        planning_year: The calendar year to generate monthly periods for.

    Returns:
        A DataFrame with columns ['Sold to ID', 'Ship to ID', 'Material ID', 'Date', 'Price']
        containing exactly 12 rows (monthly periods) per base price combination.
    """

    periods = [
        pd.Period(f"{planning_year}-{month:02d}", freq="M")
        for month in range(1, 13)
    ]

    records = []

    # Process each unique base price combination
    for _, row in base_prices.iterrows():
        cust_id = row["Sold to ID"]
        ship_id = row["Ship to ID"]
        mat_id = row["Material ID"]
        base_price = row["Price"]

        # Filter overrides matching this specific combination
        combo_overrides = [
            ov
            for ov in overrides
            if ov.material_id == mat_id
            and ov.sold_to_id == cust_id
            and ov.ship_to_id == ship_id
        ]

        # Resolve price for each month in the planning horizon
        for period in periods:
            # Find overrides that are active for the current period (start_month <= period)
            active_overrides = [
                ov for ov in combo_overrides if ov.start_month <= period
            ]

            if active_overrides:
                # Select the latest override (max start_month)
                latest_override = max(
                    active_overrides, key=lambda ov: ov.start_month
                )
                resolved_price = latest_override.new_price
            else:
                resolved_price = base_price

            records.append(
                {
                    "Sold to ID": cust_id,
                    "Ship to ID": ship_id,
                    "Material ID": mat_id,
                    "Date": period,
                    "Price": resolved_price,
                }
            )

    return pd.DataFrame(records)
