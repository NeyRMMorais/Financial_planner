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
            "Revenue": Decimal("1500.00"),
            "Total RM Cost": Decimal("500.00"),
            "Total Variable Cost": Decimal("200.00"),
            "Total Distribution Cost": Decimal("100.00"),
        },
        {
            "Material ID": "MAT-02",
            "Volume": Decimal("0.000"),
            "Revenue": Decimal("0.00"),
            "Total RM Cost": Decimal("0.00"),
            "Total Variable Cost": Decimal("0.00"),
            "Total Distribution Cost": Decimal("0.00"),
        },
        {
            "Material ID": "MAT-03",
            "Volume": Decimal("50.000"),
            "Revenue": Decimal("500.00"),
            "Total RM Cost": Decimal("600.00"),
            "Total Variable Cost": Decimal("100.00"),
            "Total Distribution Cost": Decimal("50.00"),
        },
    ]
    return pd.DataFrame(data)

def test_calculate_vcm_happy_path(base_df: pd.DataFrame) -> None:
    """Verify standard VCM logic."""
    result = calculate_vcm(base_df)

    assert "VCM" in result.columns
    assert "Unit VCM" in result.columns

    # Row 1: Normal positive VCM
    # 1500 - 500 - 200 - 100 = 700 VCM
    # Unit VCM: 700 / 100 = 7
    r1 = result.iloc[0]
    assert r1["VCM"] == Decimal("700.00")
    assert r1["Unit VCM"] == Decimal("7.00")

    # Row 2: Zero volume handling
    r2 = result.iloc[1]
    assert r2["VCM"] == Decimal("0.00")
    assert r2["Unit VCM"] == Decimal("0.00")

    # Row 3: Negative VCM
    # 500 - 600 - 100 - 50 = -250
    # Unit VCM: -250 / 50 = -5
    r3 = result.iloc[2]
    assert r3["VCM"] == Decimal("-250.00")
    assert r3["Unit VCM"] == Decimal("-5.00")

def test_calculate_vcm_missing_columns() -> None:
    """Verify that omitting a required component raises an error."""
    incomplete_df = pd.DataFrame([
        {
            "Volume": Decimal("100.000"),
            "Revenue": Decimal("1500.00"),
        }
    ])
    
    with pytest.raises(ValueError) as excinfo:
        calculate_vcm(incomplete_df)
        
    assert "Missing required columns for VCM calculation" in str(excinfo.value)
