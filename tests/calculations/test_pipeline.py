import pytest
import pandas as pd
from decimal import Decimal
from src.financial_planner.calculations.pipeline import (
    run_simulation_pipeline,
    generate_summary_metrics,
)

@pytest.fixture
def mock_pipeline_data():
    """Provides mock dataframes for all inputs to the pipeline."""
    # Volume data
    volume_df = pd.DataFrame([
        {
            "Material": "Product A",
            "Material ID": "MAT-A",
            "Plant": "PLANT-1",
            "Sold to": "Cust 1",
            "Sold to ID": "CUST-1",
            "Ship to": "Loc 1",
            "Ship to ID": "LOC-1",
            "Date": pd.Period("2026-01", freq="M"),
            "Volume": Decimal("100.000"),
        }
    ])
    
    # Resolved prices (Overrides applied) (provided in LC, EUR)
    resolved_prices = pd.DataFrame([
        {
            "Material ID": "MAT-A",
            "Sold to ID": "CUST-1",
            "Ship to ID": "LOC-1",
            "Date": pd.Period("2026-01", freq="M"),
            "Price": Decimal("9.00"),  # in EUR
        }
    ])
    
    # Base RM costs (in EUR)
    base_costs = pd.DataFrame([
        {
            "Plant": "PLANT-1",
            "Material ID": "MAT-A",
            "Date": pd.Period("2026-01", freq="M"),
            "Cost": Decimal("2.70"),  # in EUR
        }
    ])
    
    # Base Variable costs (in EUR)
    base_var_costs = pd.DataFrame([
        {
            "Material ID": "MAT-A",
            "Variable Cost": Decimal("1.80"),  # in EUR
        }
    ])
    
    # Base Distribution costs (in LC, EUR)
    base_dist_costs = pd.DataFrame([
        {
            "Ship to ID": "LOC-1",
            "Distribution Cost": Decimal("0.90"),  # in EUR
        }
    ])
    
    # Plant Currency Mapping
    plant_currency = pd.DataFrame([
        {"Plant": "PLANT-1", "Currency": "EUR"}
    ])

    # FX Rates
    fx_rates = pd.DataFrame([
        {"Period": "2026-01", "Currency": "EUR", "Rate": Decimal("0.9000"), "Date": pd.Period("2026-01", freq="M")},
        {"Period": "2026-01", "Currency": "USD", "Rate": Decimal("1.0000"), "Date": pd.Period("2026-01", freq="M")},
    ])

    return volume_df, resolved_prices, base_costs, base_var_costs, base_dist_costs, plant_currency, fx_rates

def test_run_simulation_pipeline(mock_pipeline_data):
    """Test that the pipeline orchestrates all joins and math correctly."""
    vol, prices, costs, var_costs, dist_costs, pc, fx = mock_pipeline_data
    
    result = run_simulation_pipeline(vol, prices, costs, var_costs, dist_costs, pc, fx)
    
    # EUR exchange rate = 0.90
    # Price LC = 9.00 EUR -> USD = 10.00 USD. Revenue LC = 900.00 EUR, USD = 1000.00 USD
    # RM Cost EUR = 2.70 -> USD = 3.00 USD -> LC = 2.70 EUR. Total RM Cost USD = 300.00, LC = 270.00
    # Var Cost EUR = 1.80 -> USD = 2.00 USD -> LC = 1.80 EUR. Total Var Cost USD = 200.00, LC = 180.00
    # Dist Cost LC = 0.90 EUR -> USD = 1.00 USD -> LC = 0.90 EUR. Total Dist Cost USD = 100.00, LC = 90.00
    # VCM USD = 1000 - 300 - 200 - 100 = 400.00
    # VCM LC = 900 - 270 - 180 - 90 = 360.00
    
    assert len(result) == 1
    row = result.iloc[0]
    assert row["Revenue_LC"] == Decimal("900.00")
    assert row["Revenue_USD"] == Decimal("1000.00")
    assert row["Total_RM_Cost_USD"] == Decimal("300.00")
    assert row["Total_RM_Cost_LC"] == Decimal("270.00")
    assert row["Total_Variable_Cost_USD"] == Decimal("200.00")
    assert row["Total_Variable_Cost_LC"] == Decimal("180.00")
    assert row["Total_Distribution_Cost_USD"] == Decimal("100.00")
    assert row["Total_Distribution_Cost_LC"] == Decimal("90.00")
    assert row["VCM_USD"] == Decimal("400.00")
    assert row["VCM_LC"] == Decimal("360.00")

def test_generate_summary_metrics(mock_pipeline_data):
    """Test that summary aggregations sum up row level data accurately."""
    vol, prices, costs, var_costs, dist_costs, pc, fx = mock_pipeline_data
    result = run_simulation_pipeline(vol, prices, costs, var_costs, dist_costs, pc, fx)
    
    metrics = generate_summary_metrics(result)
    
    assert metrics["total_volume"] == Decimal("100.000")
    assert metrics["total_revenue_usd"] == Decimal("1000.00")
    assert metrics["total_revenue_lc"] == Decimal("900.00")
    assert metrics["total_rm_cost_usd"] == Decimal("300.00")
    assert metrics["total_rm_cost_lc"] == Decimal("270.00")
    assert metrics["total_var_cost_usd"] == Decimal("200.00")
    assert metrics["total_var_cost_lc"] == Decimal("180.00")
    assert metrics["total_dist_cost_usd"] == Decimal("100.00")
    assert metrics["total_dist_cost_lc"] == Decimal("90.00")
    assert metrics["total_vcm_usd"] == Decimal("400.00")
    assert metrics["total_vcm_lc"] == Decimal("360.00")
    assert metrics["weighted_avg_price_usd"] == Decimal("10.00")
    assert metrics["weighted_avg_price_lc"] == Decimal("9.00")
    assert metrics["weighted_avg_vcm_usd"] == Decimal("4.00")
    assert metrics["weighted_avg_vcm_lc"] == Decimal("3.60")
