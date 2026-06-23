"""Variable Contribution Margin (VCM) calculations."""

import pandas as pd
from decimal import Decimal


def calculate_vcm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Variable Contribution Margin (VCM) in both USD and LC.
    
    VCM = Revenue - Total RM Cost - Total Variable Cost - Total Distribution Cost
    Also calculates VCM per unit (Unit VCM).
    
    Args:
        df: The DataFrame containing Revenue and all cost components.
            Must contain columns: 'Volume', 'Revenue_USD', 'Revenue_LC',
            'Total_RM_Cost_USD', 'Total_RM_Cost_LC',
            'Total_Variable_Cost_USD', 'Total_Variable_Cost_LC',
            'Total_Distribution_Cost_USD', 'Total_Distribution_Cost_LC'.
            
    Returns:
        A copy of the DataFrame with 'VCM_USD', 'VCM_LC', 'Unit_VCM_USD', and 'Unit_VCM_LC' columns added.
    """
    result_df = df.copy()

    required_columns = [
        "Volume",
        "Revenue_USD",
        "Revenue_LC",
        "Total_RM_Cost_USD",
        "Total_RM_Cost_LC",
        "Total_Variable_Cost_USD",
        "Total_Variable_Cost_LC",
        "Total_Distribution_Cost_USD",
        "Total_Distribution_Cost_LC",
    ]
    missing_cols = [col for col in required_columns if col not in result_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for VCM calculation: {missing_cols}")

    # Calculate Total VCM
    result_df["VCM_USD"] = (
        result_df["Revenue_USD"]
        - result_df["Total_RM_Cost_USD"]
        - result_df["Total_Variable_Cost_USD"]
        - result_df["Total_Distribution_Cost_USD"]
    )
    result_df["VCM_LC"] = (
        result_df["Revenue_LC"]
        - result_df["Total_RM_Cost_LC"]
        - result_df["Total_Variable_Cost_LC"]
        - result_df["Total_Distribution_Cost_LC"]
    )

    # Calculate Unit VCM safely
    def _calc_unit_vcm_usd(row: pd.Series) -> Decimal:
        if row["Volume"] > Decimal("0"):
            return row["VCM_USD"] / row["Volume"]
        return Decimal("0.00")

    def _calc_unit_vcm_lc(row: pd.Series) -> Decimal:
        if row["Volume"] > Decimal("0"):
            return row["VCM_LC"] / row["Volume"]
        return Decimal("0.00")

    result_df["Unit_VCM_USD"] = result_df.apply(_calc_unit_vcm_usd, axis=1)
    result_df["Unit_VCM_LC"] = result_df.apply(_calc_unit_vcm_lc, axis=1)

    return result_df
