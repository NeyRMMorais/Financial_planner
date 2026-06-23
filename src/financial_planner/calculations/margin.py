"""Variable Contribution Margin (VCM) calculations."""

import pandas as pd
from decimal import Decimal


def calculate_vcm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Variable Contribution Margin (VCM).
    
    VCM = Revenue - Total RM Cost - Total Variable Cost - Total Distribution Cost
    Also calculates VCM per unit (Unit VCM).
    
    Args:
        df: The DataFrame containing Revenue and all cost components.
            Must contain columns: 'Volume', 'Revenue', 'Total RM Cost', 
            'Total Variable Cost', 'Total Distribution Cost'.
            
    Returns:
        A copy of the DataFrame with 'VCM' and 'Unit VCM' columns added.
    """
    result_df = df.copy()

    required_columns = [
        "Volume",
        "Revenue",
        "Total RM Cost",
        "Total Variable Cost",
        "Total Distribution Cost",
    ]
    missing_cols = [col for col in required_columns if col not in result_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for VCM calculation: {missing_cols}")

    # Calculate Total VCM
    result_df["VCM"] = (
        result_df["Revenue"]
        - result_df["Total RM Cost"]
        - result_df["Total Variable Cost"]
        - result_df["Total Distribution Cost"]
    )

    # Calculate Unit VCM safely
    def _calc_unit_vcm(row: pd.Series) -> Decimal:
        if row["Volume"] > Decimal("0"):
            return row["VCM"] / row["Volume"]
        return Decimal("0.00")

    result_df["Unit VCM"] = result_df.apply(_calc_unit_vcm, axis=1)

    return result_df
