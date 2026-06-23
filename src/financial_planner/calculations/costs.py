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
    plant_currency_mapping_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate raw material costs for all planning combinations in EUR, USD, and LC.

    Formula:
        RM_Cost_USD = RM_Cost_EUR / Rate_EUR
        RM_Cost_LC = RM_Cost_USD * Rate_LC
        Total_RM_Cost_USD = Volume * RM_Cost_USD
        Total_RM_Cost_LC = Volume * RM_Cost_LC

    Args:
        volume_df: DataFrame with columns including:
            ['Plant', 'Material ID', 'Date', 'Volume']
        cost_df: DataFrame with columns including:
            ['Plant', 'Material ID', 'Date', 'Cost'] (in EUR)
        plant_currency_mapping_df: DataFrame with columns:
            ['Plant', 'Currency']
        fx_rates_df: DataFrame with columns:
            ['Period', 'Currency', 'Rate', 'Date']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Plant_Currency': Mapped plant local currency (if not already present).
            - 'RM_Cost_EUR': Resolved monthly raw material unit cost in EUR.
            - 'RM_Cost_USD': Resolved monthly raw material unit cost in USD.
            - 'RM_Cost_LC': Resolved monthly raw material unit cost in LC.
            - 'Total_RM_Cost_USD': Calculated total RM cost in USD.
            - 'Total_RM_Cost_LC': Calculated total RM cost in LC.

    Raises:
        ValueError: If RM costs, plant mappings, or exchange rates are missing.
    """

    if volume_df.empty:
        result = volume_df.copy()
        if "Plant_Currency" not in result.columns:
            result["Plant_Currency"] = pd.Series(dtype=str)
        result["RM_Cost_EUR"] = pd.Series(dtype=object)
        result["RM_Cost_USD"] = pd.Series(dtype=object)
        result["RM_Cost_LC"] = pd.Series(dtype=object)
        result["Total_RM_Cost_USD"] = pd.Series(dtype=object)
        result["Total_RM_Cost_LC"] = pd.Series(dtype=object)
        return result

    # Standardize types and whitespace to avoid join mismatches
    vol_clean = volume_df.copy()
    vol_clean["Plant"] = vol_clean["Plant"].astype(str).str.strip()
    vol_clean["Material ID"] = vol_clean["Material ID"].astype(str).str.strip()

    cost_clean = cost_df.copy()
    cost_clean["Plant"] = cost_clean["Plant"].astype(str).str.strip()
    cost_clean["Material ID"] = cost_clean["Material ID"].astype(str).str.strip()

    mapping_clean = plant_currency_mapping_df.copy()
    mapping_clean["Plant"] = mapping_clean["Plant"].astype(str).str.strip()
    mapping_clean["Currency"] = mapping_clean["Currency"].astype(str).str.strip()

    fx_clean = fx_rates_df.copy()
    fx_clean["Currency"] = fx_clean["Currency"].astype(str).str.strip()

    # 1. Join with Plant Currency Mapping (if not already present)
    if "Plant_Currency" not in vol_clean.columns:
        merged = pd.merge(vol_clean, mapping_clean, on="Plant", how="left")
        merged.rename(columns={"Currency": "Plant_Currency"}, inplace=True)
    else:
        merged = vol_clean

    # Validate mapping existence
    missing_mappings = merged["Plant_Currency"].isna()
    if missing_mappings.any():
        gaps = merged[missing_mappings]["Plant"].unique().tolist()
        raise ValueError(f"Missing plant currency mapping for plants: {gaps}")

    # 2. Join with monthly RM costs (provided in EUR)
    merged = pd.merge(
        merged,
        cost_clean[["Plant", "Material ID", "Date", "Cost"]],
        on=["Plant", "Material ID", "Date"],
        how="left",
    )
    merged.rename(columns={"Cost": "RM_Cost_EUR"}, inplace=True)

    # Check for missing costs
    missing_costs = merged["RM_Cost_EUR"].isna()
    if missing_costs.any():
        gaps = (
            merged[missing_costs][["Plant", "Material ID", "Date"]]
            .drop_duplicates()
            .to_dict("records")
        )
        for gap in gaps:
            gap["Date"] = str(gap["Date"])
        raise ValueError(
            f"Missing raw material unit costs for combinations: {gaps}"
        )

    # 3. Lookup Rate_EUR
    merged = pd.merge(
        merged,
        fx_clean[fx_clean["Currency"] == "EUR"][["Date", "Rate"]],
        on="Date",
        how="left",
    )
    merged.rename(columns={"Rate": "Rate_EUR"}, inplace=True)

    # Check for missing EUR rate
    missing_eur_rates = merged["Rate_EUR"].isna()
    if missing_eur_rates.any():
        gaps = merged[missing_eur_rates]["Date"].unique().tolist()
        gaps_str = [str(g) for g in gaps]
        raise ValueError(f"Missing EUR exchange rates for periods: {gaps_str}")

    # 4. Lookup Rate_LC
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

    # Check for missing LC rates
    missing_lc_rates = merged["Rate_LC"].isna()
    if missing_lc_rates.any():
        gaps = (
            merged[missing_lc_rates][["Plant_Currency", "Date"]]
            .drop_duplicates()
            .to_dict("records")
        )
        for gap in gaps:
            gap["Date"] = str(gap["Date"])
        raise ValueError(f"Missing exchange rates for currency/periods: {gaps}")

    # Perform multi-currency conversions
    merged["RM_Cost_USD"] = merged["RM_Cost_EUR"] / merged["Rate_EUR"]
    merged["RM_Cost_LC"] = merged["RM_Cost_USD"] * merged["Rate_LC"]
    merged["Total_RM_Cost_USD"] = merged["Volume"] * merged["RM_Cost_USD"]
    merged["Total_RM_Cost_LC"] = merged["Volume"] * merged["RM_Cost_LC"]

    # Drop temporary rate columns
    merged.drop(columns=["Rate_EUR", "Rate_LC"], inplace=True)

    return merged


def calculate_variable_costs(
    volume_df: pd.DataFrame,
    var_cost_df: pd.DataFrame,
    plant_currency_mapping_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate variable production costs for all planning combinations in EUR, USD, and LC.

    Formula:
        Var_Cost_USD = Var_Cost_EUR / Rate_EUR
        Var_Cost_LC = Var_Cost_USD * Rate_LC
        Total_Var_Cost_USD = Volume * Var_Cost_USD
        Total_Var_Cost_LC = Volume * Var_Cost_LC

    Args:
        volume_df: DataFrame with columns including:
            ['Material ID', 'Volume', 'Plant', 'Date']
        var_cost_df: DataFrame with columns including:
            ['Material ID', 'Variable Cost'] (in EUR)
        plant_currency_mapping_df: DataFrame with columns:
            ['Plant', 'Currency']
        fx_rates_df: DataFrame with columns:
            ['Period', 'Currency', 'Rate', 'Date']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Plant_Currency': Mapped plant local currency (if not already present).
            - 'Var_Cost_EUR': Resolved unit variable cost in EUR.
            - 'Var_Cost_USD': Resolved unit variable cost in USD per period.
            - 'Var_Cost_LC': Resolved unit variable cost in LC per period.
            - 'Total_Variable_Cost_USD': Calculated total variable cost in USD.
            - 'Total_Variable_Cost_LC': Calculated total variable cost in LC.

    Raises:
        ValueError: If variable costs, plant mappings, or exchange rates are missing.
    """

    if volume_df.empty:
        result = volume_df.copy()
        if "Plant_Currency" not in result.columns:
            result["Plant_Currency"] = pd.Series(dtype=str)
        result["Var_Cost_EUR"] = pd.Series(dtype=object)
        result["Var_Cost_USD"] = pd.Series(dtype=object)
        result["Var_Cost_LC"] = pd.Series(dtype=object)
        result["Total_Variable_Cost_USD"] = pd.Series(dtype=object)
        result["Total_Variable_Cost_LC"] = pd.Series(dtype=object)
        return result

    vol_clean = volume_df.copy()
    vol_clean["Material ID"] = vol_clean["Material ID"].astype(str).str.strip()
    vol_clean["Plant"] = vol_clean["Plant"].astype(str).str.strip()

    cost_clean = var_cost_df.copy()
    cost_clean["Material ID"] = cost_clean["Material ID"].astype(str).str.strip()

    mapping_clean = plant_currency_mapping_df.copy()
    mapping_clean["Plant"] = mapping_clean["Plant"].astype(str).str.strip()
    mapping_clean["Currency"] = mapping_clean["Currency"].astype(str).str.strip()

    fx_clean = fx_rates_df.copy()
    fx_clean["Currency"] = fx_clean["Currency"].astype(str).str.strip()

    # 1. Join with Plant Currency Mapping (if not already present)
    if "Plant_Currency" not in vol_clean.columns:
        merged = pd.merge(vol_clean, mapping_clean, on="Plant", how="left")
        merged.rename(columns={"Currency": "Plant_Currency"}, inplace=True)
    else:
        merged = vol_clean

    # Validate mapping existence
    missing_mappings = merged["Plant_Currency"].isna()
    if missing_mappings.any():
        gaps = merged[missing_mappings]["Plant"].unique().tolist()
        raise ValueError(f"Missing plant currency mapping for plants: {gaps}")

    # 2. Join with annual variable costs (provided in EUR)
    merged = pd.merge(
        merged,
        cost_clean[["Material ID", "Variable Cost"]],
        on=["Material ID"],
        how="left",
    )
    merged.rename(columns={"Variable Cost": "Var_Cost_EUR"}, inplace=True)

    # Check for missing costs
    missing_costs = merged["Var_Cost_EUR"].isna()
    if missing_costs.any():
        gaps = (
            merged[missing_costs][["Material ID"]]
            .drop_duplicates()
            .to_dict("records")
        )
        raise ValueError(f"Missing variable costs for materials: {gaps}")

    # 3. Lookup Rate_EUR for each period
    merged = pd.merge(
        merged,
        fx_clean[fx_clean["Currency"] == "EUR"][["Date", "Rate"]],
        on="Date",
        how="left",
    )
    merged.rename(columns={"Rate": "Rate_EUR"}, inplace=True)

    # Check for missing EUR rate
    missing_eur_rates = merged["Rate_EUR"].isna()
    if missing_eur_rates.any():
        gaps = merged[missing_eur_rates]["Date"].unique().tolist()
        gaps_str = [str(g) for g in gaps]
        raise ValueError(f"Missing EUR exchange rates for periods: {gaps_str}")

    # 4. Lookup Rate_LC for each period
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

    # Check for missing LC rates
    missing_lc_rates = merged["Rate_LC"].isna()
    if missing_lc_rates.any():
        gaps = (
            merged[missing_lc_rates][["Plant_Currency", "Date"]]
            .drop_duplicates()
            .to_dict("records")
        )
        for gap in gaps:
            gap["Date"] = str(gap["Date"])
        raise ValueError(f"Missing exchange rates for currency/periods: {gaps}")

    # Perform multi-currency conversions
    merged["Var_Cost_USD"] = merged["Var_Cost_EUR"] / merged["Rate_EUR"]
    merged["Var_Cost_LC"] = merged["Var_Cost_USD"] * merged["Rate_LC"]
    merged["Total_Variable_Cost_USD"] = merged["Volume"] * merged["Var_Cost_USD"]
    merged["Total_Variable_Cost_LC"] = merged["Volume"] * merged["Var_Cost_LC"]

    # Drop temporary rate columns
    merged.drop(columns=["Rate_EUR", "Rate_LC"], inplace=True)

    return merged


def calculate_distribution_costs(
    volume_df: pd.DataFrame,
    dist_cost_df: pd.DataFrame,
    plant_currency_mapping_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate annual distribution costs for all planning combinations in LC and USD.

    Formula:
        Dist_Cost_USD = Dist_Cost_LC / Rate_LC
        Total_Dist_Cost_USD = Volume * Dist_Cost_USD
        Total_Dist_Cost_LC = Volume * Dist_Cost_LC

    Args:
        volume_df: DataFrame with columns including:
            ['Ship to ID', 'Volume', 'Plant', 'Date']
        dist_cost_df: DataFrame with columns including:
            ['Ship to ID', 'Distribution Cost'] (in LC)
        plant_currency_mapping_df: DataFrame with columns:
            ['Plant', 'Currency']
        fx_rates_df: DataFrame with columns:
            ['Period', 'Currency', 'Rate', 'Date']

    Returns:
        A DataFrame containing all columns from volume_df plus:
            - 'Plant_Currency': Mapped plant local currency (if not already present).
            - 'Dist_Cost_LC': Resolved unit distribution cost in local currency.
            - 'Dist_Cost_USD': Resolved unit distribution cost in USD per period.
            - 'Total_Distribution_Cost_USD': Calculated total distribution cost in USD.
            - 'Total_Distribution_Cost_LC': Calculated total distribution cost in LC.

    Raises:
        ValueError: If distribution costs, plant mappings, or exchange rates are missing.
    """

    if volume_df.empty:
        result = volume_df.copy()
        if "Plant_Currency" not in result.columns:
            result["Plant_Currency"] = pd.Series(dtype=str)
        result["Dist_Cost_LC"] = pd.Series(dtype=object)
        result["Dist_Cost_USD"] = pd.Series(dtype=object)
        result["Total_Distribution_Cost_USD"] = pd.Series(dtype=object)
        result["Total_Distribution_Cost_LC"] = pd.Series(dtype=object)
        return result

    vol_clean = volume_df.copy()
    vol_clean["Ship to ID"] = vol_clean["Ship to ID"].astype(str).str.strip()
    vol_clean["Plant"] = vol_clean["Plant"].astype(str).str.strip()

    cost_clean = dist_cost_df.copy()
    cost_clean["Ship to ID"] = cost_clean["Ship to ID"].astype(str).str.strip()

    mapping_clean = plant_currency_mapping_df.copy()
    mapping_clean["Plant"] = mapping_clean["Plant"].astype(str).str.strip()
    mapping_clean["Currency"] = mapping_clean["Currency"].astype(str).str.strip()

    fx_clean = fx_rates_df.copy()
    fx_clean["Currency"] = fx_clean["Currency"].astype(str).str.strip()

    # 1. Join with Plant Currency Mapping (if not already present)
    if "Plant_Currency" not in vol_clean.columns:
        merged = pd.merge(vol_clean, mapping_clean, on="Plant", how="left")
        merged.rename(columns={"Currency": "Plant_Currency"}, inplace=True)
    else:
        merged = vol_clean

    # Validate mapping existence
    missing_mappings = merged["Plant_Currency"].isna()
    if missing_mappings.any():
        gaps = merged[missing_mappings]["Plant"].unique().tolist()
        raise ValueError(f"Missing plant currency mapping for plants: {gaps}")

    # 2. Join with annual distribution costs (provided in LC)
    merged = pd.merge(
        merged,
        cost_clean[["Ship to ID", "Distribution Cost"]],
        on=["Ship to ID"],
        how="left",
    )
    merged.rename(columns={"Distribution Cost": "Dist_Cost_LC"}, inplace=True)

    # Check for missing costs
    missing_costs = merged["Dist_Cost_LC"].isna()
    if missing_costs.any():
        gaps = (
            merged[missing_costs][["Ship to ID"]]
            .drop_duplicates()
            .to_dict("records")
        )
        raise ValueError(f"Missing distribution costs for Ship to destinations: {gaps}")

    # 3. Lookup Rate_LC for each period
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

    # Check for missing LC rates
    missing_lc_rates = merged["Rate_LC"].isna()
    if missing_lc_rates.any():
        gaps = (
            merged[missing_lc_rates][["Plant_Currency", "Date"]]
            .drop_duplicates()
            .to_dict("records")
        )
        for gap in gaps:
            gap["Date"] = str(gap["Date"])
        raise ValueError(f"Missing exchange rates for currency/periods: {gaps}")

    # Perform multi-currency conversions
    merged["Dist_Cost_USD"] = merged["Dist_Cost_LC"] / merged["Rate_LC"]
    merged["Total_Distribution_Cost_USD"] = merged["Volume"] * merged["Dist_Cost_USD"]
    merged["Total_Distribution_Cost_LC"] = merged["Volume"] * merged["Dist_Cost_LC"]

    # Drop temporary rate columns
    merged.drop(columns=["Rate_LC"], inplace=True)

    return merged
