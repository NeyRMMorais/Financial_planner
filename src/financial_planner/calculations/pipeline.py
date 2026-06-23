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
    plant_currency_mapping_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Execute the entire financial calculation pipeline with multi-currency.

    Args:
        volume_df: Base volume demand data.
        resolved_prices: Base pricing with overrides applied.
        base_costs: Monthly raw material costs.
        base_var_costs: Annual variable costs.
        base_dist_costs: Annual distribution costs.
        plant_currency_mapping_df: Plant to currency mappings.
        fx_rates_df: Monthly exchange rates relative to USD.

    Returns:
        A unified pd.DataFrame containing all volumes, revenues, costs, and margins in USD and LC.
    """
    revenue_df = calculate_revenue(
        volume_df, resolved_prices, plant_currency_mapping_df, fx_rates_df
    )
    rm_calc_df = calculate_rm_costs(
        revenue_df, base_costs, plant_currency_mapping_df, fx_rates_df
    )
    var_calc_df = calculate_variable_costs(
        rm_calc_df, base_var_costs, plant_currency_mapping_df, fx_rates_df
    )
    dist_calc_df = calculate_distribution_costs(
        var_calc_df, base_dist_costs, plant_currency_mapping_df, fx_rates_df
    )
    vcm_df = calculate_vcm(dist_calc_df)

    return vcm_df


def generate_summary_metrics(calculated_df: pd.DataFrame) -> Dict[str, Decimal]:
    """
    Compute aggregate summary metrics from the fully calculated dataset in USD and LC.

    Args:
        calculated_df: The final output dataframe from run_simulation_pipeline.

    Returns:
        A dictionary containing total and average metric values as Decimal objects.
    """
    total_volume = sum(calculated_df["Volume"], Decimal("0.000"))
    
    total_revenue_usd = sum(calculated_df["Revenue_USD"], Decimal("0.00"))
    total_revenue_lc = sum(calculated_df["Revenue_LC"], Decimal("0.00"))
    
    total_rm_cost_usd = sum(calculated_df["Total_RM_Cost_USD"], Decimal("0.00"))
    total_rm_cost_lc = sum(calculated_df["Total_RM_Cost_LC"], Decimal("0.00"))
    
    total_var_cost_usd = sum(calculated_df["Total_Variable_Cost_USD"], Decimal("0.00"))
    total_var_cost_lc = sum(calculated_df["Total_Variable_Cost_LC"], Decimal("0.00"))
    
    total_dist_cost_usd = sum(calculated_df["Total_Distribution_Cost_USD"], Decimal("0.00"))
    total_dist_cost_lc = sum(calculated_df["Total_Distribution_Cost_LC"], Decimal("0.00"))
    
    total_vcm_usd = sum(calculated_df["VCM_USD"], Decimal("0.00"))
    total_vcm_lc = sum(calculated_df["VCM_LC"], Decimal("0.00"))

    # Safeguards against division by zero
    weighted_avg_price_usd = (
        total_revenue_usd / total_volume if total_volume > 0 else Decimal("0.00")
    )
    weighted_avg_price_lc = (
        total_revenue_lc / total_volume if total_volume > 0 else Decimal("0.00")
    )
    
    weighted_avg_vcm_usd = (
        total_vcm_usd / total_volume if total_volume > 0 else Decimal("0.00")
    )
    weighted_avg_vcm_lc = (
        total_vcm_lc / total_volume if total_volume > 0 else Decimal("0.00")
    )

    return {
        "total_volume": total_volume,
        "total_revenue_usd": total_revenue_usd,
        "total_revenue_lc": total_revenue_lc,
        "total_rm_cost_usd": total_rm_cost_usd,
        "total_rm_cost_lc": total_rm_cost_lc,
        "total_var_cost_usd": total_var_cost_usd,
        "total_var_cost_lc": total_var_cost_lc,
        "total_dist_cost_usd": total_dist_cost_usd,
        "total_dist_cost_lc": total_dist_cost_lc,
        "total_vcm_usd": total_vcm_usd,
        "total_vcm_lc": total_vcm_lc,
        "weighted_avg_price_usd": weighted_avg_price_usd,
        "weighted_avg_price_lc": weighted_avg_price_lc,
        "weighted_avg_vcm_usd": weighted_avg_vcm_usd,
        "weighted_avg_vcm_lc": weighted_avg_vcm_lc,
    }
