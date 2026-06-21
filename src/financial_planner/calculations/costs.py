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


def calculate_variable_costs(
    volume_df: pd.DataFrame,
    var_cost_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate annual variable production costs for all planning combinations.

    Formula:
        Total Variable Cost = Volume * Variable Cost

    Args:
        volume_df: DataFrame with columns including:
            ['Material ID', 'Volume']
        var_cost_df: DataFrame with columns including:
            ['Material ID', 'Variable Cost']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Variable Cost': The resolved unit variable cost.
            - 'Total Variable Cost': The calculated total variable cost as a Decimal.

    Raises:
        ValueError: If variable cost configurations are missing for active combinations.
    """

    if volume_df.empty:
        result = volume_df.copy()
        result["Variable Cost"] = pd.Series(dtype=object)
        result["Total Variable Cost"] = pd.Series(dtype=object)
        return result

    vol_clean = volume_df.copy()
    vol_clean["Material ID"] = vol_clean["Material ID"].astype(str).str.strip()

    cost_clean = var_cost_df.copy()
    cost_clean["Material ID"] = cost_clean["Material ID"].astype(str).str.strip()

    merged = pd.merge(
        vol_clean,
        cost_clean[["Material ID", "Variable Cost"]],
        on=["Material ID"],
        how="left",
    )

    missing_costs = merged["Variable Cost"].isna()
    if missing_costs.any():
        gaps = (
            merged[missing_costs][["Material ID"]]
            .drop_duplicates()
            .to_dict("records")
        )
        raise ValueError(
            f"Missing variable costs for materials: {gaps}"
        )

    merged["Total Variable Cost"] = merged["Volume"] * merged["Variable Cost"]

    return merged
