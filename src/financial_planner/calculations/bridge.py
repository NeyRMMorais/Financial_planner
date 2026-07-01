"""Margin Bridge (Price-Volume-Mix with FX isolation) calculation engine."""

import pandas as pd
from decimal import Decimal
from typing import Dict, Any, List

def aggregate_scenario_data(df: pd.DataFrame) -> pd.DataFrame:
    groupby_keys = ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"]
    
    if df.empty:
        return pd.DataFrame(columns=groupby_keys + ["Volume", "Price_LC", "Unit_VCM_LC", "VCM_USD", "VCM_LC"])
        
    df_copy = df.copy()
    
    # Pre-populate missing columns for compatibility with tests
    if "Revenue_LC" not in df_copy.columns:
        if "Price_LC" in df_copy.columns:
            df_copy["Revenue_LC"] = df_copy["Price_LC"] * df_copy["Volume"]
        else:
            df_copy["Revenue_LC"] = Decimal("0.00")
            
    if "VCM_LC" not in df_copy.columns:
        if "Unit_VCM_LC" in df_copy.columns:
            df_copy["VCM_LC"] = df_copy["Unit_VCM_LC"] * df_copy["Volume"]
        else:
            df_copy["VCM_LC"] = Decimal("0.00")
            
    for col in ["Revenue_USD", "Total_RM_Cost_LC", "Total_Variable_Cost_LC", "Total_Distribution_Cost_LC"]:
        if col not in df_copy.columns:
            df_copy[col] = Decimal("0.00")
            
    agg = df_copy.groupby(groupby_keys, as_index=False).agg({
        "Volume": "sum",
        "Revenue_LC": "sum",
        "Revenue_USD": "sum",
        "Total_RM_Cost_LC": "sum",
        "Total_Variable_Cost_LC": "sum",
        "Total_Distribution_Cost_LC": "sum",
        "VCM_USD": "sum",
        "VCM_LC": "sum"
    })
    
    def calc_unit_price(row):
        vol = row["Volume"]
        if vol > Decimal("0") or vol > 0:
            return row["Revenue_LC"] / vol
        return Decimal("0.00")
        
    def calc_unit_vcm(row):
        vol = row["Volume"]
        if vol > Decimal("0") or vol > 0:
            return row["VCM_LC"] / vol
        return Decimal("0.00")
        
    agg["Price_LC"] = agg.apply(calc_unit_price, axis=1)
    agg["Unit_VCM_LC"] = agg.apply(calc_unit_vcm, axis=1)
    
    return agg

def calculate_margin_bridge(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    fx_rates_a: pd.DataFrame,
    fx_rates_b: pd.DataFrame,
) -> pd.DataFrame:
    """
    Decompose the difference in Variable Contribution Margin (VCM) in USD
    between Scenario A (Base) and Scenario B (Target) into Volume, Price,
    Cost, and FX effects.

    Args:
        df_a: Fully calculated output dataframe for Scenario A.
        df_b: Fully calculated output dataframe for Scenario B.
        fx_rates_a: Exchange rates for Scenario A.
        fx_rates_b: Exchange rates for Scenario B.

    Returns:
        A DataFrame containing the row-by-row bridge components in USD:
        ['Material ID', 'Sold to ID', 'Ship to ID', 'Date', 'Plant', 'Plant_Currency',
         'Volume_A', 'Volume_B', 'VCM_USD_A', 'VCM_USD_B',
         'Volume_Effect', 'Price_Effect', 'Cost_Effect', 'FX_Effect']
    """
    # 1. Aggregate and prepare copies
    a = aggregate_scenario_data(df_a)
    b = aggregate_scenario_data(df_b)

    # Clean exchange rates
    fx_a = fx_rates_a.copy()
    fx_a["Currency"] = fx_a["Currency"].astype(str).str.strip()
    fx_b = fx_rates_b.copy()
    fx_b["Currency"] = fx_b["Currency"].astype(str).str.strip()

    # 2. Merge FX rates to get the rate for each row
    # Merge Rate_A
    a = pd.merge(
        a,
        fx_a[["Date", "Currency", "Rate"]],
        left_on=["Date", "Plant_Currency"],
        right_on=["Date", "Currency"],
        how="left",
    )
    a.rename(columns={"Rate": "Rate_A"}, inplace=True)
    if "Currency" in a.columns:
        a.drop(columns=["Currency"], inplace=True)
    a.loc[a["Plant_Currency"] == "USD", "Rate_A"] = Decimal("1.0")

    # Merge Rate_B
    b = pd.merge(
        b,
        fx_b[["Date", "Currency", "Rate"]],
        left_on=["Date", "Plant_Currency"],
        right_on=["Date", "Currency"],
        how="left",
    )
    b.rename(columns={"Rate": "Rate_B"}, inplace=True)
    if "Currency" in b.columns:
        b.drop(columns=["Currency"], inplace=True)
    b.loc[b["Plant_Currency"] == "USD", "Rate_B"] = Decimal("1.0")

    # 3. Rename columns to avoid collisions
    cols_a = {
        "Volume": "Vol_A",
        "Price_LC": "Price_LC_A",
        "Unit_VCM_LC": "Unit_VCM_LC_A",
        "VCM_USD": "VCM_USD_A",
    }
    a.rename(columns=cols_a, inplace=True)

    cols_b = {
        "Volume": "Vol_B",
        "Price_LC": "Price_LC_B",
        "Unit_VCM_LC": "Unit_VCM_LC_B",
        "VCM_USD": "VCM_USD_B",
    }
    b.rename(columns=cols_b, inplace=True)

    # Keep necessary columns
    keys = ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"]
    a_subset = a[keys + list(cols_a.values()) + ["Rate_A"]]
    b_subset = b[keys + list(cols_b.values()) + ["Rate_B"]]

    # 4. Outer Join on the keys
    # Merge keys to do outer join
    merged = pd.merge(
        a_subset,
        b_subset,
        on=["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"],
        how="outer",
    )

    # 5. Fill missing values (NaNs) and handle align
    def fill_nan_decimal(series, default=Decimal("0.0")):
        return series.apply(lambda x: default if pd.isna(x) else Decimal(str(x)))

    merged["Vol_A"] = fill_nan_decimal(merged["Vol_A"])
    merged["Vol_B"] = fill_nan_decimal(merged["Vol_B"])
    merged["VCM_USD_A"] = fill_nan_decimal(merged["VCM_USD_A"])
    merged["VCM_USD_B"] = fill_nan_decimal(merged["VCM_USD_B"])

    # Align Price, Unit VCM, and Rate for new/discontinued combinations
    def align_rows(row):
        # A exists but B is missing
        if pd.isna(row["Rate_B"]):
            rate_b = Decimal(str(row["Rate_A"]))
            price_lc_b = Decimal(str(row["Price_LC_A"]))
            vcm_lc_b = Decimal(str(row["Unit_VCM_LC_A"]))
            rate_a = Decimal(str(row["Rate_A"]))
            price_lc_a = Decimal(str(row["Price_LC_A"]))
            vcm_lc_a = Decimal(str(row["Unit_VCM_LC_A"]))
        # B exists but A is missing
        elif pd.isna(row["Rate_A"]):
            rate_a = Decimal(str(row["Rate_B"]))
            price_lc_a = Decimal(str(row["Price_LC_B"]))
            vcm_lc_a = Decimal(str(row["Unit_VCM_LC_B"]))
            rate_b = Decimal(str(row["Rate_B"]))
            price_lc_b = Decimal(str(row["Price_LC_B"]))
            vcm_lc_b = Decimal(str(row["Unit_VCM_LC_B"]))
        else:
            rate_a = Decimal(str(row["Rate_A"]))
            rate_b = Decimal(str(row["Rate_B"]))
            price_lc_a = Decimal(str(row["Price_LC_A"]))
            price_lc_b = Decimal(str(row["Price_LC_B"]))
            vcm_lc_a = Decimal(str(row["Unit_VCM_LC_A"]))
            vcm_lc_b = Decimal(str(row["Unit_VCM_LC_B"]))

        return pd.Series([rate_a, rate_b, price_lc_a, price_lc_b, vcm_lc_a, vcm_lc_b])

    aligned_cols = [
        "Rate_A_aligned",
        "Rate_B_aligned",
        "Price_LC_A_aligned",
        "Price_LC_B_aligned",
        "Unit_VCM_LC_A_aligned",
        "Unit_VCM_LC_B_aligned",
    ]
    merged[aligned_cols] = merged.apply(align_rows, axis=1)

    # 6. Compute unit costs in Local Currency (C_LC = Price_LC - Unit_VCM_LC)
    merged["C_LC_A"] = merged["Price_LC_A_aligned"] - merged["Unit_VCM_LC_A_aligned"]
    merged["C_LC_B"] = merged["Price_LC_B_aligned"] - merged["Unit_VCM_LC_B_aligned"]

    # 7. Compute the bridge effects row-by-row
    # Unit VCM in USD for base scenario
    merged["Unit_VCM_USD_A"] = merged["Unit_VCM_LC_A_aligned"] / merged["Rate_A_aligned"]
    merged["Unit_VCM_USD_B"] = merged["Unit_VCM_LC_B_aligned"] / merged["Rate_B_aligned"]

    # Volume Effect = (Vol_B - Vol_A) * Unit_VCM_USD_A
    merged["Volume_Effect"] = (merged["Vol_B"] - merged["Vol_A"]) * merged["Unit_VCM_USD_A"]

    # Price Effect = Vol_B * ((Price_LC_B - Price_LC_A) / Rate_A)
    merged["Price_Effect"] = merged["Vol_B"] * (
        (merged["Price_LC_B_aligned"] - merged["Price_LC_A_aligned"]) / merged["Rate_A_aligned"]
    )

    # Cost Effect = Vol_B * ((C_LC_A - C_LC_B) / Rate_A)
    merged["Cost_Effect"] = merged["Vol_B"] * (
        (merged["C_LC_A"] - merged["C_LC_B"]) / merged["Rate_A_aligned"]
    )

    # FX Effect = Vol_B * Unit_VCM_LC_B * (1/Rate_B - 1/Rate_A)
    merged["FX_Effect"] = merged["Vol_B"] * merged["Unit_VCM_LC_B_aligned"] * (
        (Decimal("1.0") / merged["Rate_B_aligned"]) - (Decimal("1.0") / merged["Rate_A_aligned"])
    )

    # Clean up intermediate aligned columns
    merged.drop(
        columns=[
            "Rate_A_aligned",
            "Rate_B_aligned",
            "Price_LC_A_aligned",
            "Price_LC_B_aligned",
            "Unit_VCM_LC_A_aligned",
            "Unit_VCM_LC_B_aligned",
            "C_LC_A",
            "C_LC_B",
            "Unit_VCM_USD_A",
            "Unit_VCM_USD_B",
            "Rate_A",
            "Rate_B",
        ],
        inplace=True,
    )

    return merged

def summarize_margin_bridge(bridge_df: pd.DataFrame) -> Dict[str, Decimal]:
    """
    Aggregate individual row-by-row bridge effects to produce total sums in USD.
    """
    if bridge_df.empty:
        return {
            "vcm_usd_a": Decimal("0.00"),
            "volume_effect": Decimal("0.00"),
            "price_effect": Decimal("0.00"),
            "cost_effect": Decimal("0.00"),
            "fx_effect": Decimal("0.00"),
            "vcm_usd_b": Decimal("0.00"),
        }

    return {
        "vcm_usd_a": sum(bridge_df["VCM_USD_A"], Decimal("0.00")),
        "volume_effect": sum(bridge_df["Volume_Effect"], Decimal("0.00")),
        "price_effect": sum(bridge_df["Price_Effect"], Decimal("0.00")),
        "cost_effect": sum(bridge_df["Cost_Effect"], Decimal("0.00")),
        "fx_effect": sum(bridge_df["FX_Effect"], Decimal("0.00")),
        "vcm_usd_b": sum(bridge_df["VCM_USD_B"], Decimal("0.00")),
    }
