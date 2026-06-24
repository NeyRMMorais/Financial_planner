"""Unit tests for the FastAPI API routes."""

import json
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from src.financial_planner.api.main import app
from src.financial_planner.data_ingestion.scenario_manager import SCENARIOS_DIR

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_baseline_scenario():
    """Fixture to temporarily populate Baseline scenario with mock files for API testing."""
    import shutil
    from pathlib import Path
    
    baseline_dir = SCENARIOS_DIR / "Baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Backup existing files in Baseline scenario
    backup_dir = SCENARIOS_DIR / "Baseline_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir()
    
    for f in baseline_dir.iterdir():
        if f.is_file():
            shutil.copy2(f, backup_dir / f.name)
            f.unlink()
            
    # 2. Copy raw mock files to Baseline scenario
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    
    mock_files = {
        "volume_data.csv": "mock_volume_input.csv",
        "base_prices.csv": "mock_price_input.csv",
        "base_costs.csv": "mock_cost_input.csv",
        "base_var_costs.csv": "mock_variable_cost_input.csv",
        "base_dist_costs.csv": "mock_distribution_cost_input.csv",
        "fx_rates.csv": "mock_fx_rates.csv",
        "plant_currency.csv": "mock_plant_currency_mapping.csv",
    }
    
    copied = []
    for dest_name, src_name in mock_files.items():
        src_path = raw_dir / src_name
        dest_path = baseline_dir / dest_name
        if src_path.exists():
            shutil.copy2(src_path, dest_path)
            copied.append(dest_path)
            
    # Also write a basic overrides array
    overrides_path = baseline_dir / "price_overrides.json"
    with open(overrides_path, "w", encoding="utf-8") as f:
        f.write("[]")
    copied.append(overrides_path)
    
    yield
    
    # 3. Clean up copied files
    for path in copied:
        if path.exists():
            path.unlink()
            
    # 4. Restore backup files
    for f in backup_dir.iterdir():
        if f.is_file():
            shutil.copy2(f, baseline_dir / f.name)
            
    # Remove backup dir
    shutil.rmtree(backup_dir)


def test_get_scenarios():
    """Test retrieving list of scenarios."""
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Check that Baseline is always present
    scen_names = [s["name"] for s in data]
    assert "Baseline" in scen_names


def test_create_scenario():
    """Test creating a new scenario."""
    # Clean up target folder if it exists from previous run
    test_scen_dir = SCENARIOS_DIR / "TestApiScenario"
    if test_scen_dir.exists():
        import shutil
        shutil.rmtree(test_scen_dir)

    payload = {
        "name": "TestApiScenario",
        "base_scenario": "Baseline",
        "description": "Test scenario created via unit test."
    }
    response = client.post("/api/scenarios", json=payload)
    assert response.status_code == 200
    meta = response.json()
    assert meta["name"] == "TestApiScenario"
    assert meta["base_scenario"] == "Baseline"
    assert test_scen_dir.exists()

    # Clean up after test
    import shutil
    shutil.rmtree(test_scen_dir)


def test_get_scenario_data():
    """Test loading specific file data inside a scenario."""
    response = client.get("/api/scenarios/Baseline/data/fx_rates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # verify fx rate column names mapping
    first_row = data[0]
    assert "Period" in first_row
    assert "Currency" in first_row
    assert "Rate" in first_row


def test_calculate_baseline():
    """Test calculation endpoint for the Baseline scenario."""
    response = client.post("/api/scenarios/Baseline/calculate")
    assert response.status_code == 200
    res_data = response.json()
    assert "metrics" in res_data
    assert "preview" in res_data
    
    metrics = res_data["metrics"]
    assert float(metrics["total_volume"]) > 0
    assert float(metrics["total_revenue_usd"]) > 0

    preview = res_data["preview"]
    assert len(preview) > 0
    # verify output columns
    first_row = preview[0]
    assert "Revenue_USD" in first_row
    assert "VCM_USD" in first_row


def test_compare_scenarios():
    """Test scenario comparison endpoint."""
    payload = {
        "scenario_a": "Baseline",
        "scenario_b": "Baseline"
    }
    # Comparing same scenario
    response = client.post("/api/compare", json=payload)
    assert response.status_code == 200
    diff = response.json()
    assert "change_log" in diff
    # absolute diff should be all 0 since they are identical
    abs_diff = diff["absolute_diff"]
    assert float(abs_diff["total_volume"]) == 0.0
    assert float(abs_diff["total_revenue_usd"]) == 0.0


def test_diff_scenario_file():
    """Test dry-run diff check for scenario files."""
    # Create simple mock CSV contents for exchange rates
    csv_data = "Period,Currency,Rate\n2026-01,EUR,0.92\n2026-02,EUR,0.91\n"
    files = {"file": ("test_fx_rates.csv", csv_data, "text/csv")}
    
    response = client.post("/api/scenarios/Baseline/diff-file/fx_rates", files=files)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "is_new" in res_data
    assert "diff" in res_data
    assert isinstance(res_data["diff"], list)
