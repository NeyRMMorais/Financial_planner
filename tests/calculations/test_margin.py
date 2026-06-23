import pytest
import pandas as pd
from decimal import Decimal
from src.financial_planner.calculations.margin import calculate_vcm

@pytest.fixture
def base_df() -> pd.DataFrame:
    """Fixture providing a mock dataframe with required VCM calculation components."""
    data = [
        {
            "Material ID": "MAT-01",
            "Volume": Decimal("100.000"),
            "Revenue_USD": Decimal("1500.00"),
            "Revenue_LC": Decimal("3000.00"),
            "Total_RM_Cost_USD": Decimal("500.00"),
            "Total_RM_Cost_LC": Decimal("1000.00"),
            "Total_Variable_Cost_USD": Decimal("200.00"),
            "Total_Variable_Cost_LC": Decimal("400.00"),
            "Total_Distribution_Cost_USD": Decimal("100.00"),
            "Total_Distribution_Cost_LC": Decimal("200.00"),
        },
        {
            "Material ID": "MAT-02",
            "Volume": Decimal("0.000"),
            "Revenue_USD": Decimal("0.00"),
            "Revenue_LC": Decimal("0.00"),
            "Total_RM_Cost_USD": Decimal("0.00"),
            "Total_RM_Cost_LC": Decimal("0.00"),
            "Total_Variable_Cost_USD": Decimal("0.00"),
            "Total_Variable_Cost_LC": Decimal("0.00"),
            "Total_Distribution_Cost_USD": Decimal("0.00"),
            "Total_Distribution_Cost_LC": Decimal("0.00"),
        },
        {
            "Material ID": "MAT-03",
            "Volume": Decimal("50.000"),
            "Revenue_USD": Decimal("500.00"),
            "Revenue_LC": Decimal("1000.00"),
            "Total_RM_Cost_USD": Decimal("600.00"),
            "Total_RM_Cost_LC": Decimal("1200.00"),
            "Total_Variable_Cost_USD": Decimal("100.00"),
            "Total_Variable_Cost_LC": Decimal("200.00"),
            "Total_Distribution_Cost_USD": Decimal("50.00"),
            "Total_Distribution_Cost_LC": Decimal("100.00"),
        },
    ]
    return pd.DataFrame(data)

def test_calculate_vcm_happy_path(base_df: pd.DataFrame) -> None:
    """Verify standard VCM logic."""
    result = calculate_vcm(base_df)

    assert "VCM_USD" in result.columns
    assert "VCM_LC" in result.columns
    assert "Unit_VCM_USD" in result.columns
    assert "Unit_VCM_LC" in result.columns

    # Row 1: Normal positive VCM
    # USD: 1500 - 500 - 200 - 100 = 700 VCM, Unit VCM: 7.00
    # LC: 3000 - 1000 - 400 - 200 = 1400 VCM, Unit VCM: 14.00
    r1 = result.iloc[0]
    assert r1["VCM_USD"] == Decimal("700.00")
    assert r1["VCM_LC"] == Decimal("1400.00")
    assert r1["Unit_VCM_USD"] == Decimal("7.00")
    assert r1["Unit_VCM_LC"] == Decimal("14.00")

    # Row 2: Zero volume handling
    r2 = result.iloc[1]
    assert r2["VCM_USD"] == Decimal("0.00")
    assert r2["VCM_LC"] == Decimal("0.00")
    assert r2["Unit_VCM_USD"] == Decimal("0.00")
    assert r2["Unit_VCM_LC"] == Decimal("0.00")

    # Row 3: Negative VCM
    # USD: 500 - 600 - 100 - 50 = -250, Unit VCM: -5.00
    # LC: 1000 - 1200 - 200 - 100 = -500, Unit VCM: -10.00
    r3 = result.iloc[2]
    assert r3["VCM_USD"] == Decimal("-250.00")
    assert r3["VCM_LC"] == Decimal("-500.00")
    assert r3["Unit_VCM_USD"] == Decimal("-5.00")
    assert r3["Unit_VCM_LC"] == Decimal("-10.00")

def test_calculate_vcm_missing_columns() -> None:
    """Verify that omitting a required component raises an error."""
    incomplete_df = pd.DataFrame([
        {
            "Volume": Decimal("100.000"),
            "Revenue_USD": Decimal("1500.00"),
        }
    ])
    
    with pytest.raises(ValueError) as excinfo:
        calculate_vcm(incomplete_df)
        
    assert "Missing required columns for VCM calculation" in str(excinfo.value)
