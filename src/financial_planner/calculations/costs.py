"""Raw material cost calculations.

This module defines functions for calculating monthly raw material costs based on
sales volumes and monthly plant-specific raw material costs.
"""

from __future__ import annotations

from decimal import Decimal
import pandas as pd


def calculate_rm_costs(
    volume_df: pd.DataFrame,
    cost_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate raw material costs for all planning combinations.

    Formula:
        Total RM Cost = Volume * Unit Cost (Cost)

    Both Volume and Cost must be Decimals. The calculated Total RM Cost will
    also be a Decimal. If any combination/period lacks a configured raw material
    cost, a ValueError is raised.

    Args:
        volume_df: DataFrame with columns including:
            ['Plant', 'Material ID', 'Date', 'Volume']
        cost_df: DataFrame with columns including:
            ['Plant', 'Material ID', 'Date', 'Cost']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Cost': The resolved monthly raw material unit cost.
            - 'Total RM Cost': The calculated total RM cost as a Decimal.

    Raises:
        ValueError: If raw material cost configurations are missing for active combinations/periods.
    """

    if volume_df.empty:
        result = volume_df.copy()
        result["Cost"] = pd.Series(dtype=object)
        result["Total RM Cost"] = pd.Series(dtype=object)
        return result

    # Standardize types and whitespace to avoid join mismatches
    vol_clean = volume_df.copy()
    vol_clean["Plant"] = vol_clean["Plant"].astype(str).str.strip()
    vol_clean["Material ID"] = vol_clean["Material ID"].astype(str).str.strip()

    cost_clean = cost_df.copy()
    cost_clean["Plant"] = cost_clean["Plant"].astype(str).str.strip()
    cost_clean["Material ID"] = cost_clean["Material ID"].astype(str).str.strip()

    # Join on ['Plant', 'Material ID', 'Date']
    merged = pd.merge(
        vol_clean,
        cost_clean[["Plant", "Material ID", "Date", "Cost"]],
        on=["Plant", "Material ID", "Date"],
        how="left",
    )

    # Check for missing costs
    missing_costs = merged["Cost"].isna()
    if missing_costs.any():
        gaps = (
            merged[missing_costs][["Plant", "Material ID", "Date"]]
            .drop_duplicates()
            .to_dict("records")
        )
        # Format the Date object to string in the error message for readability
        for gap in gaps:
            gap["Date"] = str(gap["Date"])
        raise ValueError(
            f"Missing raw material unit costs for combinations: {gaps}"
        )

    # Perform exact Decimal multiplication
    merged["Total RM Cost"] = merged["Volume"] * merged["Cost"]

    return merged
