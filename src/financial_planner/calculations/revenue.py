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
    plant_currency_mapping_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate the revenue for all planning combinations in both LC and USD.

    Formula:
        Price_USD = Price_LC / Rate_LC
        Revenue_LC = Volume * Price_LC
        Revenue_USD = Volume * Price_USD

    Both Volume and Price must be Decimals. The calculated Revenue will also
    be a Decimal. If any volume combination lacks a resolved price, a
    ValueError is raised.

    Args:
        volume_df: DataFrame with columns including:
            ['Sold to ID', 'Ship to ID', 'Material ID', 'Date', 'Volume', 'Plant']
        resolved_prices_df: DataFrame with columns including:
            ['Sold to ID', 'Ship to ID', 'Material ID', 'Date', 'Price']
        plant_currency_mapping_df: DataFrame with columns:
            ['Plant', 'Currency']
        fx_rates_df: DataFrame with columns:
            ['Period', 'Currency', 'Rate', 'Date']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Plant_Currency': The local currency code.
            - 'Price_LC': The resolved unit price in local currency.
            - 'Price_USD': The resolved unit price in USD.
            - 'Revenue_LC': The calculated revenue in local currency.
            - 'Revenue_USD': The calculated revenue in USD.

    Raises:
        ValueError: If there are missing prices, plant mapping, or exchange rates.
    """

    # Check for empty inputs to return an empty DataFrame with the correct schema
    if volume_df.empty:
        result = volume_df.copy()
        result["Plant_Currency"] = pd.Series(dtype=str)
        result["Price_LC"] = pd.Series(dtype=object)
        result["Price_USD"] = pd.Series(dtype=object)
        result["Revenue_LC"] = pd.Series(dtype=object)
        result["Revenue_USD"] = pd.Series(dtype=object)
        return result

    # Standardize types and whitespace to avoid join mismatches
    vol_clean = volume_df.copy()
    vol_clean["Sold to ID"] = vol_clean["Sold to ID"].astype(str).str.strip()
    vol_clean["Ship to ID"] = vol_clean["Ship to ID"].astype(str).str.strip()
    vol_clean["Material ID"] = vol_clean["Material ID"].astype(str).str.strip()
    vol_clean["Plant"] = vol_clean["Plant"].astype(str).str.strip()

    price_clean = resolved_prices_df.copy()
    price_clean["Sold to ID"] = price_clean["Sold to ID"].astype(str).str.strip()
    price_clean["Ship to ID"] = price_clean["Ship to ID"].astype(str).str.strip()
    price_clean["Material ID"] = price_clean["Material ID"].astype(str).str.strip()

    mapping_clean = plant_currency_mapping_df.copy()
    mapping_clean["Plant"] = mapping_clean["Plant"].astype(str).str.strip()
    mapping_clean["Currency"] = mapping_clean["Currency"].astype(str).str.strip()

    fx_clean = fx_rates_df.copy()
    fx_clean["Currency"] = fx_clean["Currency"].astype(str).str.strip()

    # 1. Merge volume with Plant Currency Mapping
    merged = pd.merge(vol_clean, mapping_clean, on="Plant", how="left")
    merged.rename(columns={"Currency": "Plant_Currency"}, inplace=True)

    # Validate mapping existence
    missing_mappings = merged["Plant_Currency"].isna()
    if missing_mappings.any():
        gaps = merged[missing_mappings]["Plant"].unique().tolist()
        raise ValueError(f"Missing plant currency mapping for plants: {gaps}")

    # 2. Merge with Price (uploaded in LC)
    merged = pd.merge(
        merged,
        price_clean[["Sold to ID", "Ship to ID", "Material ID", "Date", "Price"]],
        on=["Sold to ID", "Ship to ID", "Material ID", "Date"],
        how="left",
    )
    merged.rename(columns={"Price": "Price_LC"}, inplace=True)

    # Check for any volume combinations that couldn't find a matching price
    missing_prices = merged["Price_LC"].isna()
    if missing_prices.any():
        gaps = (
            merged[missing_prices][["Sold to ID", "Ship to ID", "Material ID"]]
            .drop_duplicates()
            .to_dict("records")
        )
        raise ValueError(
            f"Missing unit pricing configuration for combinations: {gaps}"
        )

    # 3. Merge for FX Rate (Rate_LC)
    merged = pd.merge(
        merged,
        fx_clean[["Date", "Currency", "Rate"]],
        left_on=["Date", "Plant_Currency"],
        right_on=["Date", "Currency"],
        how="left",
    )
    merged.rename(columns={"Rate": "Rate_LC"}, inplace=True)
    merged.drop(columns=["Currency"], inplace=True)

    # Safe fallback: if currency is USD, rate is 1.0
    merged.loc[merged["Plant_Currency"] == "USD", "Rate_LC"] = Decimal("1.0")

    # Check for missing rates
    missing_rates = merged["Rate_LC"].isna()
    if missing_rates.any():
        gaps = (
            merged[missing_rates][["Plant_Currency", "Date"]]
            .drop_duplicates()
            .to_dict("records")
        )
        for gap in gaps:
            gap["Date"] = str(gap["Date"])
        raise ValueError(f"Missing exchange rates for currency/periods: {gaps}")

    # Calculations
    merged["Price_USD"] = merged["Price_LC"] / merged["Rate_LC"]
    merged["Revenue_LC"] = merged["Volume"] * merged["Price_LC"]
    merged["Revenue_USD"] = merged["Volume"] * merged["Price_USD"]

    # Drop temporary rate columns
    merged.drop(columns=["Rate_LC"], inplace=True)

    return merged
