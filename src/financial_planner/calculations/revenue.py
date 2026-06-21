"""Revenue calculation engine.

This module defines functions for calculating planning revenue based on monthly
sales volumes and resolved monthly unit prices.
"""

from __future__ import annotations

from decimal import Decimal
import pandas as pd


def calculate_revenue(
    volume_df: pd.DataFrame,
    resolved_prices_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate the revenue for all planning combinations.

    Formula:
        Revenue = Volume * Price

    Both Volume and Price must be Decimals. The calculated Revenue will also
    be a Decimal. If any volume combination lacks a resolved price, a
    ValueError is raised.

    Args:
        volume_df: DataFrame with columns including:
            ['Sold to ID', 'Ship to ID', 'Material ID', 'Date', 'Volume']
        resolved_prices_df: DataFrame with columns including:
            ['Sold to ID', 'Ship to ID', 'Material ID', 'Date', 'Price']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Price': The resolved unit price.
            - 'Revenue': The calculated revenue as a Decimal.

    Raises:
        ValueError: If there are missing prices for active planned volume combinations.
    """

    # Check for empty inputs to return an empty DataFrame with the correct schema
    if volume_df.empty:
        result = volume_df.copy()
        result["Price"] = pd.Series(dtype=object)
        result["Revenue"] = pd.Series(dtype=object)
        return result

    # Standardize types and whitespace to avoid join mismatches
    vol_clean = volume_df.copy()
    vol_clean["Sold to ID"] = vol_clean["Sold to ID"].astype(str).str.strip()
    vol_clean["Ship to ID"] = vol_clean["Ship to ID"].astype(str).str.strip()
    vol_clean["Material ID"] = vol_clean["Material ID"].astype(str).str.strip()

    price_clean = resolved_prices_df.copy()
    price_clean["Sold to ID"] = price_clean["Sold to ID"].astype(str).str.strip()
    price_clean["Ship to ID"] = price_clean["Ship to ID"].astype(str).str.strip()
    price_clean["Material ID"] = price_clean["Material ID"].astype(str).str.strip()

    # Perform a left join on the planning grain
    merged = pd.merge(
        vol_clean,
        price_clean[["Sold to ID", "Ship to ID", "Material ID", "Date", "Price"]],
        on=["Sold to ID", "Ship to ID", "Material ID", "Date"],
        how="left",
    )

    # Check for any volume combinations that couldn't find a matching price
    missing_prices = merged["Price"].isna()
    if missing_prices.any():
        gaps = (
            merged[missing_prices][["Sold to ID", "Ship to ID", "Material ID"]]
            .drop_duplicates()
            .to_dict("records")
        )
        raise ValueError(
            f"Missing unit pricing configuration for combinations: {gaps}"
        )

    # Perform exact Decimal multiplication element-wise
    merged["Revenue"] = merged["Volume"] * merged["Price"]

    return merged
