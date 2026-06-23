"""Unit tests for the scenario manager module."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

import src.financial_planner.data_ingestion.scenario_manager as sm


@pytest.fixture
def mock_scenarios_dir(tmp_path: Path, monkeypatch) -> Path:
    """Fixture to redirect the scenario directories to a temp path for testing."""
    scenarios_dir = tmp_path / "scenarios"
    raw_dir = tmp_path / "raw"
    scenarios_dir.mkdir()
    raw_dir.mkdir()

    # Create dummy raw files for Baseline initialization testing
    (raw_dir / "mock_volume_input.csv").write_text(
        "Material,Material ID,Date,Sold to ID,Sold to,Ship to ID,Ship to,Plant,Volume\n"
        "Product A,MAT-1,2026-01,CUST-1,Customer 1,SHIP-1,Ship To 1,PLANT-01,10.0\n"
    )
    (raw_dir / "mock_price_input.csv").write_text(
        "Sold to ID,Ship to ID,Material ID,Price\n"
        "CUST-1,SHIP-1,MAT-1,5.00\n"
    )
    (raw_dir / "mock_cost_input.csv").write_text(
        "Plant,Material ID,Period,Cost\n"
        "PLANT-01,MAT-1,2026-01,3.00\n"
    )
    (raw_dir / "mock_variable_cost_input.csv").write_text(
        "Material,Material ID,Variable Cost\n"
        "Product A,MAT-1,1.00\n"
    )
    (raw_dir / "mock_distribution_cost_input.csv").write_text(
        "Ship to,Ship to ID,Distribution Cost\n"
        "Ship To 1,SHIP-1,0.50\n"
    )
    (raw_dir / "mock_fx_rates.csv").write_text(
        "Period,Currency,Rate\n"
        "2026-01,EUR,0.9000\n"
        "2026-01,USD,1.0000\n"
    )
    (raw_dir / "mock_plant_currency_mapping.csv").write_text(
        "Plant,Currency\n"
        "PLANT-01,EUR\n"
    )

    monkeypatch.setattr(sm, "SCENARIOS_DIR", scenarios_dir)
    monkeypatch.setattr(sm, "RAW_DIR", raw_dir)
    return scenarios_dir


def test_ensure_baseline_exists(mock_scenarios_dir: Path) -> None:
    """Test that default Baseline scenario is auto-created with metadata."""
    sm.ensure_baseline_exists()
    baseline_dir = mock_scenarios_dir / "Baseline"
    
    assert baseline_dir.exists()
    assert (baseline_dir / "volume_data.csv").exists()
    assert (baseline_dir / "price_overrides.json").exists()
    assert (baseline_dir / "metadata.json").exists()

    with open(baseline_dir / "metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["name"] == "Baseline"
    assert meta["base_scenario"] is None


def test_list_scenarios(mock_scenarios_dir: Path) -> None:
    """Test that list_scenarios successfully lists and orders existing scenarios."""
    sm.ensure_baseline_exists()
    sm.create_scenario("Scenario_A", base_scenario="Baseline", description="Test scenario A")
    
    scenarios = sm.list_scenarios()
    assert len(scenarios) == 2
    assert scenarios[0]["name"] == "Baseline"
    assert scenarios[1]["name"] == "Scenario_A"
    assert scenarios[1]["base_scenario"] == "Baseline"
    assert scenarios[1]["description"] == "Test scenario A"


def test_create_scenario_scratch_and_clone(mock_scenarios_dir: Path) -> None:
    """Test scenario creation from scratch and cloning from another scenario."""
    sm.ensure_baseline_exists()

    # 1. From scratch (no base)
    meta_scratch = sm.create_scenario("Scratch_Scen")
    assert meta_scratch["name"] == "Scratch_Scen"
    assert meta_scratch["base_scenario"] is None
    assert (mock_scenarios_dir / "Scratch_Scen" / "price_overrides.json").exists()

    # 2. Cloned from Baseline
    meta_clone = sm.create_scenario("Cloned_Scen", base_scenario="Baseline")
    assert meta_clone["name"] == "Cloned_Scen"
    assert meta_clone["base_scenario"] == "Baseline"
    # Should copy Baseline files
    assert (mock_scenarios_dir / "Cloned_Scen" / "volume_data.csv").exists()

    # 3. Duplicate name error
    with pytest.raises(ValueError, match="already exists"):
        sm.create_scenario("Scratch_Scen")


def test_save_and_load_scenario(mock_scenarios_dir: Path) -> None:
    """Test loading and saving all 8 inputs to a scenario directory."""
    sm.ensure_baseline_exists()
    sm.create_scenario("Scenario_X", base_scenario="Baseline")

    # Load initial copied baseline data
    data = sm.load_scenario_data("Scenario_X")
    assert data["volume_data"] is not None
    assert len(data["volume_data"]) == 1
    assert data["volume_data"].loc[0, "Volume"] == Decimal("10.0")

    # Modify volume and add a price override
    data["volume_data"].loc[0, "Volume"] = Decimal("15.5")
    data["price_overrides"] = [
        {
            "Material ID": "MAT-1",
            "Sold to ID": "CUST-1",
            "Ship to ID": "SHIP-1",
            "Date": pd.Period("2026-02", freq="M"),
            "Price": Decimal("9.99"),
        }
    ]

    # Save
    sm.save_scenario_data("Scenario_X", data)

    # Reload and verify
    reloaded = sm.load_scenario_data("Scenario_X")
    assert reloaded["volume_data"].loc[0, "Volume"] == Decimal("15.5")
    assert len(reloaded["price_overrides"]) == 1
    assert reloaded["price_overrides"][0]["Price"] == Decimal("9.99")
    assert reloaded["price_overrides"][0]["Date"] == pd.Period("2026-02", freq="M")


def test_compute_dataframe_diff(mock_scenarios_dir: Path) -> None:
    """Test row-level difference generation between two datasets."""
    # 1. Base df
    df_base = pd.DataFrame([
        {"ID": "A", "Val": 10},
        {"ID": "B", "Val": 20},
    ])
    # 2. New df: A is updated, B is deleted, C is added
    df_new = pd.DataFrame([
        {"ID": "A", "Val": 12},  # updated
        {"ID": "C", "Val": 30},  # added
    ])

    diffs = sm.diff_dataframe(df_base, df_new, ["ID"], ["Val"])
    assert len(diffs) == 3
    assert any("added" in d for d in diffs)
    assert any("deleted" in d for d in diffs)
    assert any("updated" in d for d in diffs)


def test_diff_scenarios_inputs(mock_scenarios_dir: Path) -> None:
    """Test generating a change log comparing two scenarios."""
    sm.ensure_baseline_exists()
    sm.create_scenario("Scenario_Y", base_scenario="Baseline")

    # Save without changes
    sm.save_scenario_data("Scenario_Y", sm.load_scenario_data("Scenario_Y"))
    
    with open(mock_scenarios_dir / "Scenario_Y" / "metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["change_log"] == ["No changes detected in any input files."]

    # Load and make changes
    data = sm.load_scenario_data("Scenario_Y")
    # Change variable costs
    data["base_var_costs"].loc[0, "Variable Cost"] = Decimal("1.25")
    # Save
    sm.save_scenario_data("Scenario_Y", data)

    with open(mock_scenarios_dir / "Scenario_Y" / "metadata.json", "r", encoding="utf-8") as f:
        meta2 = json.load(f)
    assert len(meta2["change_log"]) == 1
    assert "Base Var Costs" in meta2["change_log"][0]
    assert "values updated" in meta2["change_log"][0]
