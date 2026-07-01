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


def test_compare_bridge():
    """Test scenario margin bridge endpoint."""
    payload = {
        "scenario_a": "Baseline",
        "scenario_b": "Baseline"
    }
    response = client.post("/api/compare/bridge", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "summary" in res
    assert "by_material" in res
    assert "by_month" in res
    assert "raw_preview" in res

    summary = res["summary"]
    assert float(summary["volume_effect"]) == pytest.approx(0.0, abs=1e-9)
    assert float(summary["price_effect"]) == pytest.approx(0.0, abs=1e-9)
    assert float(summary["cost_effect"]) == pytest.approx(0.0, abs=1e-9)
    assert float(summary["fx_effect"]) == pytest.approx(0.0, abs=1e-9)


def test_login_log():
    """Test the login audit log endpoint."""
    payload = {
        "email": "test@company.com",
        "name": "Test User",
        "provider": "google"
    }
    response = client.post("/api/login-log", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    
    # Assert log file is created and has the user logged
    from pathlib import Path
    log_file = Path("data/login_audit.log")
    assert log_file.exists()
    
    content = log_file.read_text(encoding="utf-8")
    assert "test@company.com" in content
    assert "Test User" in content
    assert "google" in content


def test_diff_scenario_file_extended():
    """Test extended dry-run diff check returning FX and var costs deltas."""
    # Test FX
    fx_csv = "Period,Currency,Rate\n2026-01,EUR,0.95\n2026-02,EUR,0.94\n"
    fx_files = {"file": ("test_fx_rates.csv", fx_csv, "text/csv")}
    fx_resp = client.post("/api/scenarios/Baseline/diff-file/fx_rates", files=fx_files)
    assert fx_resp.status_code == 200
    fx_data = fx_resp.json()
    assert "fx_delta_by_currency" in fx_data

    # Test Var Costs
    var_csv = "Material,Material ID,Variable Cost\nProduct X,MAT-1001,4.50\n"
    var_files = {"file": ("test_var_costs.csv", var_csv, "text/csv")}
    var_resp = client.post("/api/scenarios/Baseline/diff-file/base_var_costs", files=var_files)
    assert var_resp.status_code == 200
    var_data = var_resp.json()
    assert "var_cost_delta_by_material" in var_data


def test_get_login_logs():
    """Test retrieving login logs with admin vs non-admin email."""
    # Write a test log line first to guarantee data is present
    from pathlib import Path
    log_file = Path("data/login_audit.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("[2026-07-01 13:20:00] User: Ney Morais (ney.morais@gmail.com) signed in via google\n")

    # Unauthorized email should return 403
    unauth_resp = client.get("/api/admin/login-logs?email=random@company.com")
    assert unauth_resp.status_code == 403
    assert "Forbidden" in unauth_resp.json()["detail"]

    # Authorized email should return 200 and parse log entry correctly
    auth_resp = client.get("/api/admin/login-logs?email=ney.morais@gmail.com")
    assert auth_resp.status_code == 200
    logs = auth_resp.json()
    assert len(logs) >= 1
    # Check parsing of fields
    first_log = next((l for l in logs if l["email"] == "ney.morais@gmail.com"), None)
    assert first_log is not None
    assert first_log["name"] == "Ney Morais"
    assert first_log["provider"] == "google"
    assert first_log["timestamp"] == "2026-07-01 13:20:00"


def test_export_bridge_pptx():
    """Test PowerPoint presentation export endpoint."""
    payload = {
        "scenario_a": "Baseline",
        "scenario_b": "Scenario A",
        "vcm_usd_a": 1000000.0,
        "volume_effect": 200000.0,
        "price_effect": 150000.0,
        "cost_effect": -50000.0,
        "fx_effect": 0.0,
        "vcm_usd_b": 1300000.0,
        "material_filter": "All Materials",
        "region_filter": "All Regions"
    }
    response = client.post("/api/export/bridge-pptx", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert len(response.content) > 0






