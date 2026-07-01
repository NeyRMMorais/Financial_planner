import pytest
import pandas as pd
from decimal import Decimal
from src.financial_planner.calculations.bridge import calculate_margin_bridge, summarize_margin_bridge

@pytest.fixture
def keys() -> list:
    return ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"]

@pytest.fixture
def mock_fx_rates() -> pd.DataFrame:
    # EUR is 2.0 LC per USD in scenario A, 4.0 in scenario B (exaggerated for testing)
    data = [
        {"Period": "2026-01", "Currency": "EUR", "Rate": Decimal("2.0"), "Date": "2026-01"},
        {"Period": "2026-01", "Currency": "USD", "Rate": Decimal("1.0"), "Date": "2026-01"},
    ]
    return pd.DataFrame(data)

@pytest.fixture
def mock_fx_rates_b() -> pd.DataFrame:
    # Scenario B has FX shock: EUR is 2.5 LC per USD
    data = [
        {"Period": "2026-01", "Currency": "EUR", "Rate": Decimal("2.5"), "Date": "2026-01"},
        {"Period": "2026-01", "Currency": "USD", "Rate": Decimal("1.0"), "Date": "2026-01"},
    ]
    return pd.DataFrame(data)

def test_bridge_volume_effect(mock_fx_rates, keys) -> None:
    # Scenario A
    df_a = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("2500.00"), # 100 * 50 / 2.0
        }
    ])
    # Scenario B: volume goes up to 150.000, everything else constant
    df_b = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("150.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("3750.00"), # 150 * 50 / 2.0
        }
    ])

    res = calculate_margin_bridge(df_a, df_b, mock_fx_rates, mock_fx_rates)
    row = res.iloc[0]

    # VCM A = 2500.00, VCM B = 3750.00, Delta = +1250.00
    # Vol Delta = +50.000, Unit VCM A (USD) = 50 / 2.0 = 25.00
    # Volume Effect = 50.000 * 25.00 = +1250.00
    assert row["Volume_Effect"] == Decimal("1250.00")
    assert row["Price_Effect"] == Decimal("0.00")
    assert row["Cost_Effect"] == Decimal("0.00")
    assert row["FX_Effect"] == Decimal("0.00")
    
    summary = summarize_margin_bridge(res)
    assert summary["volume_effect"] == Decimal("1250.00")
    assert summary["price_effect"] == Decimal("0.00")
    assert summary["cost_effect"] == Decimal("0.00")
    assert summary["fx_effect"] == Decimal("0.00")
    assert summary["vcm_usd_a"] == Decimal("2500.00")
    assert summary["vcm_usd_b"] == Decimal("3750.00")

def test_bridge_price_effect(mock_fx_rates, keys) -> None:
    # Scenario A
    df_a = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("2500.00"),
        }
    ])
    # Scenario B: price goes up by 20 LC to 220.00 (which increases VCM LC to 70.00), vol & cost constant
    df_b = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("220.00"),
            "Unit_VCM_LC": Decimal("70.00"), "VCM_USD": Decimal("3500.00"),
        }
    ])

    res = calculate_margin_bridge(df_a, df_b, mock_fx_rates, mock_fx_rates)
    row = res.iloc[0]

    # Price Effect = 100 * (220 - 200) / 2.0 = +1000.00
    assert row["Volume_Effect"] == Decimal("0.00")
    assert row["Price_Effect"] == Decimal("1000.00")
    assert row["Cost_Effect"] == Decimal("0.00")
    assert row["FX_Effect"] == Decimal("0.00")

def test_bridge_cost_effect(mock_fx_rates, keys) -> None:
    # Scenario A
    df_a = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("2500.00"),
        }
    ])
    # Scenario B: Unit Cost goes down by 15 LC (Unit VCM LC goes up by 15 to 65.00), vol & price constant
    df_b = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("65.00"), "VCM_USD": Decimal("3250.00"),
        }
    ])

    res = calculate_margin_bridge(df_a, df_b, mock_fx_rates, mock_fx_rates)
    row = res.iloc[0]

    # Cost Effect = 100 * (C_LC_A - C_LC_B) / 2.0
    # C_LC_A = 200 - 50 = 150
    # C_LC_B = 200 - 65 = 135
    # Cost Effect = 100 * (150 - 135) / 2.0 = +750.00
    assert row["Volume_Effect"] == Decimal("0.00")
    assert row["Price_Effect"] == Decimal("0.00")
    assert row["Cost_Effect"] == Decimal("750.00")
    assert row["FX_Effect"] == Decimal("0.00")

def test_bridge_fx_effect(mock_fx_rates, mock_fx_rates_b, keys) -> None:
    # Scenario A
    df_a = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("2500.00"), # 100 * 50 / 2.0
        }
    ])
    # Scenario B: EUR weakens from 2.0 to 2.5 per USD (everything else constant)
    df_b = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("2000.00"), # 100 * 50 / 2.5
        }
    ])

    res = calculate_margin_bridge(df_a, df_b, mock_fx_rates, mock_fx_rates_b)
    row = res.iloc[0]

    # FX Effect = 100 * 50 * (1 / 2.5 - 1 / 2.0) = 5000 * (0.4 - 0.5) = -500.00
    assert row["Volume_Effect"] == Decimal("0.00")
    assert row["Price_Effect"] == Decimal("0.00")
    assert row["Cost_Effect"] == Decimal("0.00")
    assert row["FX_Effect"] == Decimal("-500.00")

def test_bridge_full_reconciliation(mock_fx_rates, mock_fx_rates_b, keys) -> None:
    # Mix all changes
    # Scenario A
    df_a = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("100.000"), "Price_LC": Decimal("200.00"),
            "Unit_VCM_LC": Decimal("50.00"), "VCM_USD": Decimal("2500.00"), # 100 * 50 / 2.0
        }
    ])
    # Scenario B:
    # Vol goes from 100 to 120 (+20)
    # Price LC goes from 200 to 220 (+20 LC)
    # Cost LC goes from 150 to 160 (+10 LC cost increase -> -10 VCM)
    # Unit VCM LC = 220 - 160 = 60 LC
    # Rate B goes from 2.0 to 2.5 (EUR weakens)
    df_b = pd.DataFrame([
        {
            "Sold to ID": "C-1", "Ship to ID": "S-1", "Material ID": "M-1",
            "Date": "2026-01", "Plant": "P-1", "Plant_Currency": "EUR", "Material": "Mat-1",
            "Volume": Decimal("120.000"), "Price_LC": Decimal("220.00"),
            "Unit_VCM_LC": Decimal("60.00"), "VCM_USD": Decimal("2880.00"), # 120 * 60 / 2.5
        }
    ])

    res = calculate_margin_bridge(df_a, df_b, mock_fx_rates, mock_fx_rates_b)
    row = res.iloc[0]

    # Calculations:
    # Vol A = 100, Vol B = 120
    # Rate A = 2.0, Rate B = 2.5
    # Unit VCM LC A = 50, Unit VCM LC B = 60
    # Price LC A = 200, Price LC B = 220
    # C LC A = 200 - 50 = 150, C LC B = 220 - 60 = 160
    #
    # Volume Effect = (120 - 100) * (50 / 2.0) = 20 * 25 = +500.00
    # Price Effect = 120 * ((220 - 200) / 2.0) = 120 * 10 = +1200.00
    # Cost Effect = 120 * ((150 - 160) / 2.0) = 120 * (-5) = -600.00
    # FX Effect = 120 * 60 * (1 / 2.5 - 1 / 2.0) = 7200 * (-0.1) = -720.00
    #
    # Sum of effects: 500 + 1200 - 600 - 720 = +380.00
    # VCM USD B - VCM USD A = 2880 - 2500 = +380.00
    # Reconciliation is perfect!
    assert row["Volume_Effect"] == Decimal("500.00")
    assert row["Price_Effect"] == Decimal("1200.00")
    assert row["Cost_Effect"] == Decimal("-600.00")
    assert row["FX_Effect"] == Decimal("-720.00")
    
    summary = summarize_margin_bridge(res)
    assert summary["vcm_usd_a"] == Decimal("2500.00")
    assert summary["vcm_usd_b"] == Decimal("2880.00")
    assert summary["vcm_usd_a"] + summary["volume_effect"] + summary["price_effect"] + summary["cost_effect"] + summary["fx_effect"] == summary["vcm_usd_b"]
