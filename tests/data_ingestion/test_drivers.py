"""Unit tests for top-down assumption driver cascading and change log impact trail."""

import json
from decimal import Decimal
from pathlib import Path
import pytest

from src.financial_planner.data_ingestion.scenario_manager import (
    create_scenario,
    apply_scenario_drivers,
    load_scenario_data,
    SCENARIOS_DIR,
)


@pytest.fixture
def clean_test_scenario():
    name = "Test_Driver_Cascade_Scenario"
    target_dir = SCENARIOS_DIR / name
    if target_dir.exists():
        import shutil
        shutil.rmtree(target_dir)

    create_scenario(name, base_scenario="Baseline", description="Scenario for testing driver cascading")
    yield name

    if target_dir.exists():
        import shutil
        shutil.rmtree(target_dir)


def test_apply_volume_and_price_drivers(clean_test_scenario):
    name = clean_test_scenario
    
    # 1. Apply +10% price on Line 1 and +5% volume globally
    adjustments = [
        {
            "driver_type": "price",
            "scope_type": "product_line",
            "scope_value": "Line 1 - Performance Specialties",
            "adjustment_type": "pct",
            "value": Decimal("10.0"),
        },
        {
            "driver_type": "volume",
            "scope_type": "portfolio",
            "scope_value": None,
            "adjustment_type": "pct",
            "value": Decimal("5.0"),
        },
    ]

    result = apply_scenario_drivers(
        name=name,
        adjustments=adjustments,
        description="Executive what-if: +10% price on Line 1 and +5% portfolio volume",
        author="CFO User",
    )

    assert result["scenario"] == name
    assert result["applied_count"] == 2
    
    entry = result["change_log_entry"]
    assert entry["author"] == "CFO User"
    assert "Line 1" in entry["description"]
    assert Decimal(entry["vcm_after_usd"]) > Decimal(entry["vcm_before_usd"])
    assert Decimal(entry["impact_usd"]) > Decimal("0.00")
    assert "+" in entry["impact_pct"]

    # Verify metadata.json contains the impact trail
    meta_path = SCENARIOS_DIR / name / "metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    assert len(meta.get("impact_trail", [])) >= 1
    assert meta["impact_trail"][0]["id"] == entry["id"]
    assert len(meta.get("change_log", [])) >= 1


def test_apply_cost_and_fx_drivers(clean_test_scenario):
    name = clean_test_scenario

    adjustments = [
        {
            "driver_type": "raw_cost",
            "scope_type": "portfolio",
            "scope_value": None,
            "adjustment_type": "pct",
            "value": Decimal("15.0"), # +15% feedstock cost shock
        },
        {
            "driver_type": "fx_rate",
            "scope_type": "portfolio",
            "scope_value": "EUR",
            "adjustment_type": "absolute",
            "value": Decimal("1.25"),
        },
    ]

    result = apply_scenario_drivers(
        name=name,
        adjustments=adjustments,
        description="Macro shock: +15% feedstock and EUR rate 1.25",
        author="Controller",
    )

    assert result["scenario"] == name
    assert result["applied_count"] == 2
    entry = result["change_log_entry"]
    assert entry["driver"] in ("Raw Material Cost", "FX Rate", "Multi-Driver")
    
    # Reload scenario data and check FX rates
    data = load_scenario_data(name)
    eur_rates = data["fx_rates"][data["fx_rates"]["Currency"] == "EUR"]
    assert (eur_rates["Rate"] == Decimal("1.25")).all()
