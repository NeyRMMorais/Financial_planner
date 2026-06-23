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
    
    # Resolved prices (Overrides applied)
    resolved_prices = pd.DataFrame([
        {
            "Material ID": "MAT-A",
            "Sold to ID": "CUST-1",
            "Ship to ID": "LOC-1",
            "Date": pd.Period("2026-01", freq="M"),
            "Price": Decimal("10.00"),
        }
    ])
    
    # Base RM costs
    base_costs = pd.DataFrame([
        {
            "Plant": "PLANT-1",
            "Material ID": "MAT-A",
            "Date": pd.Period("2026-01", freq="M"),
            "Cost": Decimal("3.00"),
        }
    ])
    
    # Base Variable costs
    base_var_costs = pd.DataFrame([
        {
            "Material ID": "MAT-A",
            "Variable Cost": Decimal("2.00"),
        }
    ])
    
    # Base Distribution costs
    base_dist_costs = pd.DataFrame([
        {
            "Ship to ID": "LOC-1",
            "Distribution Cost": Decimal("1.00"),
        }
    ])
    
    return volume_df, resolved_prices, base_costs, base_var_costs, base_dist_costs

def test_run_simulation_pipeline(mock_pipeline_data):
    """Test that the pipeline orchestrates all joins and math correctly."""
    vol, prices, costs, var_costs, dist_costs = mock_pipeline_data
    
    result = run_simulation_pipeline(vol, prices, costs, var_costs, dist_costs)
    
    # Revenue: 100 * 10 = 1000
    # RM Cost: 100 * 3 = 300
    # Var Cost: 100 * 2 = 200
    # Dist Cost: 100 * 1 = 100
    # VCM: 1000 - 300 - 200 - 100 = 400
    
    assert len(result) == 1
    row = result.iloc[0]
    assert row["Revenue"] == Decimal("1000.00")
    assert row["Total RM Cost"] == Decimal("300.00")
    assert row["Total Variable Cost"] == Decimal("200.00")
    assert row["Total Distribution Cost"] == Decimal("100.00")
    assert row["VCM"] == Decimal("400.00")

def test_generate_summary_metrics(mock_pipeline_data):
    """Test that summary aggregations sum up row level data accurately."""
    vol, prices, costs, var_costs, dist_costs = mock_pipeline_data
    result = run_simulation_pipeline(vol, prices, costs, var_costs, dist_costs)
    
    metrics = generate_summary_metrics(result)
    
    assert metrics["total_volume"] == Decimal("100.000")
    assert metrics["total_revenue"] == Decimal("1000.00")
    assert metrics["total_rm_cost"] == Decimal("300.00")
    assert metrics["total_var_cost"] == Decimal("200.00")
    assert metrics["total_dist_cost"] == Decimal("100.00")
    assert metrics["total_vcm"] == Decimal("400.00")
    assert metrics["weighted_avg_price"] == Decimal("10.00")
    assert metrics["weighted_avg_vcm"] == Decimal("4.00")
