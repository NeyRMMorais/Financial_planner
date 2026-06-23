"""Unified calculation pipeline for the financial planner."""

import pandas as pd
from decimal import Decimal
from typing import Dict, Any

from src.financial_planner.calculations.revenue import calculate_revenue
from src.financial_planner.calculations.costs import (
    calculate_rm_costs,
    calculate_variable_costs,
    calculate_distribution_costs,
)
from src.financial_planner.calculations.margin import calculate_vcm


def run_simulation_pipeline(
    volume_df: pd.DataFrame,
    resolved_prices: pd.DataFrame,
    base_costs: pd.DataFrame,
    base_var_costs: pd.DataFrame,
    base_dist_costs: pd.DataFrame,
) -> pd.DataFrame:
    """
    Execute the entire financial calculation pipeline.

    Args:
        volume_df: Base volume demand data.
        resolved_prices: Base pricing with overrides applied.
        base_costs: Monthly raw material costs.
        base_var_costs: Annual variable costs.
        base_dist_costs: Annual distribution costs.

    Returns:
        A unified pd.DataFrame containing all volumes, revenues, costs, and margins.
    """
    revenue_df = calculate_revenue(volume_df, resolved_prices)
    rm_calc_df = calculate_rm_costs(revenue_df, base_costs)
    var_calc_df = calculate_variable_costs(rm_calc_df, base_var_costs)
    dist_calc_df = calculate_distribution_costs(var_calc_df, base_dist_costs)
    vcm_df = calculate_vcm(dist_calc_df)

    return vcm_df


def generate_summary_metrics(calculated_df: pd.DataFrame) -> Dict[str, Decimal]:
    """
    Compute aggregate summary metrics from the fully calculated dataset.

    Args:
        calculated_df: The final output dataframe from run_simulation_pipeline.

    Returns:
        A dictionary containing total and average metric values as Decimal objects.
    """
    total_volume = sum(calculated_df["Volume"], Decimal("0.000"))
    total_revenue = sum(calculated_df["Revenue"], Decimal("0.00"))
    total_rm_cost = sum(calculated_df["Total RM Cost"], Decimal("0.00"))
    total_var_cost = sum(calculated_df["Total Variable Cost"], Decimal("0.00"))
    total_dist_cost = sum(calculated_df["Total Distribution Cost"], Decimal("0.00"))
    total_vcm = sum(calculated_df["VCM"], Decimal("0.00"))

    # Safeguards against division by zero
    weighted_avg_price = (
        total_revenue / total_volume if total_volume > 0 else Decimal("0.00")
    )
    weighted_avg_vcm = total_vcm / total_volume if total_volume > 0 else Decimal("0.00")

    return {
        "total_volume": total_volume,
        "total_revenue": total_revenue,
        "total_rm_cost": total_rm_cost,
        "total_var_cost": total_var_cost,
        "total_dist_cost": total_dist_cost,
        "total_vcm": total_vcm,
        "weighted_avg_price": weighted_avg_price,
        "weighted_avg_vcm": weighted_avg_vcm,
    }
