"""FastAPI routes for the financial planner API layer."""

from io import StringIO
import io
import math
from pathlib import Path
from decimal import Decimal
from typing import List, Literal
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
import pandas as pd

from src.financial_planner.api.schemas import (
    ScenarioCreate,
    ScenarioMetadataResponse,
    PriceOverrideInput,
    SimulationMetrics,
    CalculationResponse,
    CompareRequest,
    ScenarioDifference,
    LoginLogInput,
)
from src.financial_planner.data_ingestion.scenario_manager import (
    list_scenarios,
    create_scenario,
    load_scenario_data,
    save_scenario_data,
    diff_scenarios_inputs,
    diff_dataframe,
    SCENARIOS_DIR,
    FILE_MAP,
)
from src.financial_planner.data_ingestion.cost_loader import load_cost_data
from src.financial_planner.data_ingestion.data_loader import load_planning_volume_data
from src.financial_planner.data_ingestion.distribution_cost_loader import load_distribution_cost_data
from src.financial_planner.data_ingestion.fx_loader import load_fx_data, load_plant_currency_data
from src.financial_planner.data_ingestion.price_loader import load_pricing_data
from src.financial_planner.data_ingestion.variable_cost_loader import load_variable_cost_data
from src.financial_planner.calculations.pricing import PriceOverride, resolve_monthly_prices
from src.financial_planner.calculations.pipeline import run_simulation_pipeline, generate_summary_metrics
from src.financial_planner.calculations.bridge import calculate_margin_bridge, summarize_margin_bridge
from src.financial_planner.api.schemas import BridgeResponse

router = APIRouter()


def df_to_records(df: pd.DataFrame) -> List[dict]:
    """Helper to convert a DataFrame to JSON-serializable records."""
    if df is None:
        return []
    df_copy = df.copy()
    for col in df_copy.columns:
        # Convert Period values to strings
        df_copy[col] = df_copy[col].apply(
            lambda val: str(val) if isinstance(val, pd.Period) else val
        )
        # Convert Decimal values to float for JSON serialization
        df_copy[col] = df_copy[col].apply(
            lambda val: float(val) if isinstance(val, Decimal) else val
        )
    # Convert NaNs to None (null in JSON)
    return df_copy.where(pd.notnull(df_copy), None).to_dict(orient="records")


def add_files_status(s: dict) -> dict:
    """Helper to dynamically populate the file upload/completeness status."""
    name = s["name"]
    scen_dir = SCENARIOS_DIR / name
    files_status = {}
    for file_type, file_name in FILE_MAP.items():
        file_path = scen_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            if file_type == "price_overrides":
                files_status[file_type] = size > 4
            else:
                files_status[file_type] = size > 0
        else:
            files_status[file_type] = False
    s["files_status"] = files_status
    return s


@router.get("/scenarios", response_model=List[ScenarioMetadataResponse])
def get_scenarios():
    """List all available scenarios."""
    try:
        scenarios = list_scenarios()
        return [add_files_status(s) for s in scenarios]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenarios", response_model=ScenarioMetadataResponse)
def create_new_scenario(payload: ScenarioCreate):
    """Create a new scenario, optionally cloning from a base scenario."""
    try:
        s = create_scenario(payload.name, payload.base_scenario, payload.description)
        return add_files_status(s)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios/{name}/metadata", response_model=ScenarioMetadataResponse)
def get_scenario_metadata(name: str):
    """Fetch scenario metadata and change log."""
    scenarios = list_scenarios()
    for s in scenarios:
        if s["name"] == name:
            return add_files_status(s)
    raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found.")



@router.get("/scenarios/{name}/data/{file_type}")
def get_scenario_file_data(name: str, file_type: str):
    """Fetch raw or override records for a specific scenario input file."""
    if file_type not in FILE_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")

    try:
        data = load_scenario_data(name)
        file_data = data.get(file_type)

        if file_type == "price_overrides":
            # For price_overrides, convert elements to UI format
            overrides = []
            for item in file_data:
                overrides.append({
                    "Material ID": item.get("Material ID"),
                    "Sold to ID": item.get("Sold to ID"),
                    "Ship to ID": item.get("Ship to ID"),
                    "Date": str(item.get("Date")) if item.get("Date") else None,
                    "Price": float(item.get("Price")) if isinstance(item.get("Price"), Decimal) else item.get("Price")
                })
            return overrides

        if file_data is not None:
            return df_to_records(file_data.head(100))
        return []
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenarios/{name}/overrides")
def update_price_overrides(name: str, overrides: List[PriceOverrideInput]):
    """Update and save price overrides list for a scenario."""
    try:
        # Load existing scenario data
        scen_data = load_scenario_data(name)
        
        # Format the Pydantic models to the dictionary format expected by the scenario manager
        formatted_overrides = []
        for item in overrides:
            formatted_overrides.append({
                "Material ID": item.material_id,
                "Sold to ID": item.sold_to_id,
                "Ship to ID": item.ship_to_id,
                "Date": pd.Period(item.date, freq="M"),
                "Price": item.price,
            })
        
        scen_data["price_overrides"] = formatted_overrides
        save_scenario_data(name, scen_data)
        return {"status": "success", "message": "Price overrides updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenarios/{name}/upload/{file_type}")
async def upload_scenario_file(name: str, file_type: str, file: UploadFile = File(...)):
    """Upload and overwrite a scenario input CSV file after validation."""
    if file_type not in FILE_MAP or file_type == "price_overrides":
        raise HTTPException(status_code=400, detail=f"Invalid CSV file type: {file_type}")

    scen_dir = SCENARIOS_DIR / name
    if not scen_dir.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' does not exist.")

    contents = await file.read()
    string_data = contents.decode("utf-8")
    io_data = StringIO(string_data)

    try:
        # Validate data by loading it through respective schema loaders
        if file_type == "volume_data":
            load_planning_volume_data(io_data)
        elif file_type == "base_prices":
            load_pricing_data(io_data)
        elif file_type == "base_costs":
            load_cost_data(io_data)
        elif file_type == "base_var_costs":
            load_variable_cost_data(io_data)
        elif file_type == "base_dist_costs":
            load_distribution_cost_data(io_data)
        elif file_type == "fx_rates":
            load_fx_data(io_data)
        elif file_type == "plant_currency":
            load_plant_currency_data(io_data)

        # If loading succeeded with no exceptions, write to disk
        dest_path = scen_dir / FILE_MAP[file_type]
        with open(dest_path, "wb") as f:
            f.write(contents)

        # Trigger auto change log recalculation by resaving the scenario
        scen_data = load_scenario_data(name)
        save_scenario_data(name, scen_data)

        return {"status": "success", "message": f"{file_type} uploaded and validated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post("/scenarios/{name}/diff-file/{file_type}")
async def diff_scenario_file(name: str, file_type: str, file: UploadFile = File(...)):
    """Dry-run validation and comparison between the existing scenario file and a newly selected CSV file."""
    if file_type not in FILE_MAP or file_type == "price_overrides":
        raise HTTPException(status_code=400, detail=f"Invalid CSV file type: {file_type}")

    scen_dir = SCENARIOS_DIR / name
    if not scen_dir.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' does not exist.")

    contents = await file.read()
    string_data = contents.decode("utf-8")
    io_data = StringIO(string_data)

    try:
        # 1. Parse and validate the new file
        df_new = None
        if file_type == "volume_data":
            df_new = load_planning_volume_data(io_data)
        elif file_type == "base_prices":
            df_new = load_pricing_data(io_data)
        elif file_type == "base_costs":
            df_new = load_cost_data(io_data)
        elif file_type == "base_var_costs":
            df_new = load_variable_cost_data(io_data)
        elif file_type == "base_dist_costs":
            df_new = load_distribution_cost_data(io_data)
        elif file_type == "fx_rates":
            df_new = load_fx_data(io_data)
        elif file_type == "plant_currency":
            df_new = load_plant_currency_data(io_data)

        # 2. Get keys and value columns for comparison
        configs_dict = {
            "volume_data": (["Material ID", "Plant", "Sold to ID", "Ship to ID", "Date"], ["Volume"]),
            "base_prices": (["Sold to ID", "Ship to ID", "Material ID"], ["Price"]),
            "base_costs": (["Plant", "Material ID", "Date"], ["Cost"]),
            "base_var_costs": (["Material ID"], ["Variable Cost"]),
            "base_dist_costs": (["Ship to ID"], ["Distribution Cost"]),
            "fx_rates": (["Period", "Currency"], ["Rate"]),
            "plant_currency": (["Plant"], ["Currency"]),
        }

        keys, val_cols = configs_dict[file_type]

        # 3. Load the existing file
        scen_data = load_scenario_data(name)
        df_base = scen_data.get(file_type)

        # 4. Generate diff logs
        diff_logs = diff_dataframe(df_base, df_new, keys, val_cols)

        # If base is None, it means it's a completely new file upload
        is_new = df_base is None

        # 5. For volume_data: compute per-material volume delta (MT)
        volume_delta_by_material = None
        if file_type == "volume_data" and df_new is not None:
            # Sum volumes by Material ID in new file
            new_by_mat = (
                df_new.groupby("Material ID")["Volume"]
                .sum()
                .reset_index()
                .rename(columns={"Volume": "new_volume"})
            )
            if df_base is not None:
                base_by_mat = (
                    df_base.groupby("Material ID")["Volume"]
                    .sum()
                    .reset_index()
                    .rename(columns={"Volume": "base_volume"})
                )
                merged = pd.merge(base_by_mat, new_by_mat, on="Material ID", how="outer")
                merged["base_volume"] = merged["base_volume"].fillna(Decimal("0.000"))
                merged["new_volume"] = merged["new_volume"].fillna(Decimal("0.000"))
                merged["delta"] = merged["new_volume"] - merged["base_volume"]
            else:
                merged = new_by_mat.copy()
                merged["base_volume"] = Decimal("0.000")
                merged["delta"] = merged["new_volume"]

            # Convert Decimal to float for JSON serialisation
            volume_delta_by_material = [
                {
                    "material_id": row["Material ID"],
                    "base_volume": float(row["base_volume"]),
                    "new_volume": float(row["new_volume"]),
                    "delta": float(row["delta"]),
                }
                for _, row in merged.iterrows()
                if float(row["delta"]) != 0.0  # only include changed materials
            ]
            # Sort by absolute delta descending
            volume_delta_by_material.sort(key=lambda x: abs(x["delta"]), reverse=True)

        # 6. For base_prices: compute per-material average price delta
        price_delta_by_material = None
        if file_type == "base_prices" and df_new is not None:
            new_avg = (
                df_new.groupby("Material ID")["Price"]
                .apply(lambda s: s.sum() / Decimal(len(s)) if len(s) > 0 else Decimal("0.000"))
                .reset_index()
                .rename(columns={"Price": "new_avg_price"})
            )
            if df_base is not None:
                base_avg = (
                    df_base.groupby("Material ID")["Price"]
                    .apply(lambda s: s.sum() / Decimal(len(s)) if len(s) > 0 else Decimal("0.000"))
                    .reset_index()
                    .rename(columns={"Price": "base_avg_price"})
                )
                merged_p = pd.merge(base_avg, new_avg, on="Material ID", how="outer")
                merged_p["base_avg_price"] = merged_p["base_avg_price"].fillna(Decimal("0.000"))
                merged_p["new_avg_price"] = merged_p["new_avg_price"].fillna(Decimal("0.000"))
                merged_p["delta"] = merged_p["new_avg_price"] - merged_p["base_avg_price"]
            else:
                merged_p = new_avg.copy()
                merged_p["base_avg_price"] = Decimal("0.000")
                merged_p["delta"] = merged_p["new_avg_price"]

            price_delta_by_material = [
                {
                    "material_id": row["Material ID"],
                    "base_avg_price": float(row["base_avg_price"]),
                    "new_avg_price": float(row["new_avg_price"]),
                    "delta": float(row["delta"]),
                    "pct_change": (
                        round(float(row["delta"]) / float(row["base_avg_price"]) * 100, 2)
                        if float(row["base_avg_price"]) != 0.0 else None
                    ),
                }
                for _, row in merged_p.iterrows()
                if float(row["delta"]) != 0.0
            ]
            # Sort by absolute delta descending
            price_delta_by_material.sort(key=lambda x: abs(x["delta"]), reverse=True)

        # 7. For base_var_costs: compute per-material variable cost delta
        var_cost_delta_by_material = None
        if file_type == "base_var_costs" and df_new is not None:
            new_v = (
                df_new.groupby("Material ID")["Variable Cost"]
                .apply(lambda s: s.sum() / Decimal(len(s)) if len(s) > 0 else Decimal("0.000"))
                .reset_index()
                .rename(columns={"Variable Cost": "new_var_cost"})
            )
            if df_base is not None:
                base_v = (
                    df_base.groupby("Material ID")["Variable Cost"]
                    .apply(lambda s: s.sum() / Decimal(len(s)) if len(s) > 0 else Decimal("0.000"))
                    .reset_index()
                    .rename(columns={"Variable Cost": "base_var_cost"})
                )
                merged_v = pd.merge(base_v, new_v, on="Material ID", how="outer")
                merged_v["base_var_cost"] = merged_v["base_var_cost"].fillna(Decimal("0.000"))
                merged_v["new_var_cost"] = merged_v["new_var_cost"].fillna(Decimal("0.000"))
                merged_v["delta"] = merged_v["new_var_cost"] - merged_v["base_var_cost"]
            else:
                merged_v = new_v.copy()
                merged_v["base_var_cost"] = Decimal("0.000")
                merged_v["delta"] = merged_v["new_var_cost"]

            var_cost_delta_by_material = [
                {
                    "material_id": row["Material ID"],
                    "base_var_cost": float(row["base_var_cost"]),
                    "new_var_cost": float(row["new_var_cost"]),
                    "delta": float(row["delta"]),
                }
                for _, row in merged_v.iterrows()
                if float(row["delta"]) != 0.0
            ]
            var_cost_delta_by_material.sort(key=lambda x: abs(x["delta"]), reverse=True)

        # 8. For fx_rates: compute per-currency average rate delta
        fx_delta_by_currency = None
        if file_type == "fx_rates" and df_new is not None:
            new_f = (
                df_new.groupby("Currency")["Rate"]
                .apply(lambda s: s.sum() / Decimal(len(s)) if len(s) > 0 else Decimal("0.0000"))
                .reset_index()
                .rename(columns={"Rate": "new_rate"})
            )
            if df_base is not None:
                base_f = (
                    df_base.groupby("Currency")["Rate"]
                    .apply(lambda s: s.sum() / Decimal(len(s)) if len(s) > 0 else Decimal("0.0000"))
                    .reset_index()
                    .rename(columns={"Rate": "base_rate"})
                )
                merged_f = pd.merge(base_f, new_f, on="Currency", how="outer")
                merged_f["base_rate"] = merged_f["base_rate"].fillna(Decimal("0.0000"))
                merged_f["new_rate"] = merged_f["new_rate"].fillna(Decimal("0.0000"))
                merged_f["delta"] = merged_f["new_rate"] - merged_f["base_rate"]
            else:
                merged_f = new_f.copy()
                merged_f["base_rate"] = Decimal("0.0000")
                merged_f["delta"] = merged_f["new_rate"]

            fx_delta_by_currency = [
                {
                    "currency": row["Currency"],
                    "base_rate": float(row["base_rate"]),
                    "new_rate": float(row["new_rate"]),
                    "delta": float(row["delta"]),
                }
                for _, row in merged_f.iterrows()
                if float(row["delta"]) != 0.0
            ]
            fx_delta_by_currency.sort(key=lambda x: abs(x["delta"]), reverse=True)

        return {
            "status": "success",
            "is_new": is_new,
            "diff": diff_logs,
            "volume_delta_by_material": volume_delta_by_material,
            "price_delta_by_material": price_delta_by_material,
            "var_cost_delta_by_material": var_cost_delta_by_material,
            "fx_delta_by_currency": fx_delta_by_currency,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@router.post("/scenarios/{name}/save")
def trigger_scenario_save(name: str):
    """Recalculate auto-change logs and save scenario state."""
    try:
        data = load_scenario_data(name)
        save_scenario_data(name, data)
        return {"status": "success", "message": f"Scenario '{name}' saved successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenarios/{name}/calculate", response_model=CalculationResponse)
def calculate_scenario(name: str):
    """Run simulation pipeline and return USD/LC aggregates and calculated preview."""
    try:
        data = load_scenario_data(name)
        
        # Verify all input datasets are loaded
        missing = [k for k, v in data.items() if v is None and k != "price_overrides"]
        if missing:
            raise HTTPException(status_code=400, detail=f"Scenario has missing files: {missing}")

        # Convert price overrides dict list to PriceOverride classes
        price_overrides_list = []
        for item in data["price_overrides"]:
            price_overrides_list.append(PriceOverride(
                material_id=item["Material ID"],
                sold_to_id=item["Sold to ID"],
                ship_to_id=item["Ship to ID"],
                start_month=item["Date"],
                new_price=item["Price"]
            ))

        resolved_prices = resolve_monthly_prices(data["base_prices"], price_overrides_list)
        
        df_calc = run_simulation_pipeline(
            volume_df=data["volume_data"],
            resolved_prices=resolved_prices,
            base_costs=data["base_costs"],
            base_var_costs=data["base_var_costs"],
            base_dist_costs=data["base_dist_costs"],
            plant_currency_mapping_df=data["plant_currency"],
            fx_rates_df=data["fx_rates"],
        )

        metrics = generate_summary_metrics(df_calc)
        preview_records = df_to_records(df_calc.head(100))

        return {
            "metrics": metrics,
            "preview": preview_records
        }
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/scenarios/{name}/export")
def export_scenario_sac(name: str):
    """Export the SAC-ready CSV for the scenario."""
    try:
        data = load_scenario_data(name)
        missing = [k for k, v in data.items() if v is None and k != "price_overrides"]
        if missing:
            raise HTTPException(status_code=400, detail=f"Scenario has missing files: {missing}")

        price_overrides_list = []
        for item in data["price_overrides"]:
            price_overrides_list.append(PriceOverride(
                material_id=item["Material ID"],
                sold_to_id=item["Sold to ID"],
                ship_to_id=item["Ship to ID"],
                start_month=item["Date"],
                new_price=item["Price"]
            ))

        resolved_prices = resolve_monthly_prices(data["base_prices"], price_overrides_list)
        
        df_calc = run_simulation_pipeline(
            volume_df=data["volume_data"],
            resolved_prices=resolved_prices,
            base_costs=data["base_costs"],
            base_var_costs=data["base_var_costs"],
            base_dist_costs=data["base_dist_costs"],
            plant_currency_mapping_df=data["plant_currency"],
            fx_rates_df=data["fx_rates"],
        )

        # Write to memory buffer
        stream = io.StringIO()
        df_calc.to_csv(stream, index=False)
        response = StreamingResponse(
            io.BytesIO(stream.getvalue().encode("utf-8")),
            media_type="text/csv",
        )
        response.headers["Content-Disposition"] = f"attachment; filename=calculated_revenue_and_rm_cost_{name}.csv"
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/compare", response_model=ScenarioDifference)
def compare_two_scenarios(payload: CompareRequest):
    """Compare two scenarios side-by-side, returning metrics deltas and VCM variances."""
    scen_a = payload.scenario_a
    scen_b = payload.scenario_b

    try:
        data_a = load_scenario_data(scen_a)
        data_b = load_scenario_data(scen_b)

        missing_a = [k for k, v in data_a.items() if v is None and k != "price_overrides"]
        missing_b = [k for k, v in data_b.items() if v is None and k != "price_overrides"]

        if missing_a:
            raise HTTPException(status_code=400, detail=f"Scenario A is incomplete: {missing_a}")
        if missing_b:
            raise HTTPException(status_code=400, detail=f"Scenario B is incomplete: {missing_b}")

        # Run Scenario A
        over_list_a = [PriceOverride(item["Material ID"], item["Sold to ID"], item["Ship to ID"], item["Date"], item["Price"]) for item in data_a["price_overrides"]]
        prices_res_a = resolve_monthly_prices(data_a["base_prices"], over_list_a)
        df_calc_a = run_simulation_pipeline(
            data_a["volume_data"], prices_res_a, data_a["base_costs"],
            data_a["base_var_costs"], data_a["base_dist_costs"],
            data_a["plant_currency"], data_a["fx_rates"]
        )
        metrics_a = generate_summary_metrics(df_calc_a)

        # Run Scenario B
        over_list_b = [PriceOverride(item["Material ID"], item["Sold to ID"], item["Ship to ID"], item["Date"], item["Price"]) for item in data_b["price_overrides"]]
        prices_res_b = resolve_monthly_prices(data_b["base_prices"], over_list_b)
        df_calc_b = run_simulation_pipeline(
            data_b["volume_data"], prices_res_b, data_b["base_costs"],
            data_b["base_var_costs"], data_b["base_dist_costs"],
            data_b["plant_currency"], data_b["fx_rates"]
        )
        metrics_b = generate_summary_metrics(df_calc_b)

        # Absolute Delta
        abs_diff = {}
        compare_keys = [
            "total_volume",
            "total_revenue_usd",
            "total_rm_cost_usd",
            "total_var_cost_usd",
            "total_dist_cost_usd",
            "total_vcm_usd",
            "weighted_avg_price_usd",
            "weighted_avg_vcm_usd",
        ]
        for key in compare_keys:
            abs_diff[key] = metrics_b[key] - metrics_a[key]

        # Percentage Delta
        pct_diff = {}
        for key in compare_keys:
            val_a = metrics_a[key]
            delta = metrics_b[key] - val_a
            pct_diff[key] = f"{(delta / val_a * 100):+.1f}%" if val_a != 0 else "0.0%"

        # Plant VCM Variance
        plant_a = df_calc_a.groupby("Plant")[["Volume", "VCM_USD"]].sum().reset_index()
        plant_b = df_calc_b.groupby("Plant")[["Volume", "VCM_USD"]].sum().reset_index()
        plant_merged = pd.merge(plant_a, plant_b, on="Plant", suffixes=("_A", "_B"), how="outer").fillna(0)
        plant_merged["Volume Delta"] = plant_merged["Volume_B"] - plant_merged["Volume_A"]
        plant_merged["VCM Delta"] = plant_merged["VCM_USD_B"] - plant_merged["VCM_USD_A"]
        plant_variance = df_to_records(plant_merged)

        # Material VCM Variance
        mat_a = df_calc_a.groupby(["Material", "Material ID"])[["Volume", "VCM_USD"]].sum().reset_index()
        mat_b = df_calc_b.groupby(["Material", "Material ID"])[["Volume", "VCM_USD"]].sum().reset_index()
        mat_merged = pd.merge(mat_a, mat_b, on=["Material", "Material ID"], suffixes=("_A", "_B"), how="outer").fillna(0)
        mat_merged["Volume Delta"] = mat_merged["Volume_B"] - mat_merged["Volume_A"]
        mat_merged["VCM Delta"] = mat_merged["VCM_USD_B"] - mat_merged["VCM_USD_A"]
        mat_variance = df_to_records(mat_merged)

        # Diff logs
        diff_logs = diff_scenarios_inputs(scen_a, scen_b)

        return {
            "absolute_diff": abs_diff,
            "percentage_diff": pct_diff,
            "change_log": diff_logs,
            "vcm_variance_by_plant": plant_variance,
            "vcm_variance_by_material": mat_variance,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post("/compare/bridge", response_model=BridgeResponse)
def compare_bridge(payload: CompareRequest):
    """Calculate PVM + FX margin bridge between two scenarios."""
    scen_a = payload.scenario_a
    scen_b = payload.scenario_b

    try:
        data_a = load_scenario_data(scen_a)
        data_b = load_scenario_data(scen_b)

        missing_a = [k for k, v in data_a.items() if v is None and k != "price_overrides"]
        missing_b = [k for k, v in data_b.items() if v is None and k != "price_overrides"]

        if missing_a:
            raise HTTPException(status_code=400, detail=f"Scenario A is incomplete: {missing_a}")
        if missing_b:
            raise HTTPException(status_code=400, detail=f"Scenario B is incomplete: {missing_b}")

        # Run Scenario A
        over_list_a = [PriceOverride(item["Material ID"], item["Sold to ID"], item["Ship to ID"], item["Date"], item["Price"]) for item in data_a["price_overrides"]]
        prices_res_a = resolve_monthly_prices(data_a["base_prices"], over_list_a)
        df_calc_a = run_simulation_pipeline(
            data_a["volume_data"], prices_res_a, data_a["base_costs"],
            data_a["base_var_costs"], data_a["base_dist_costs"],
            data_a["plant_currency"], data_a["fx_rates"]
        )

        # Run Scenario B
        over_list_b = [PriceOverride(item["Material ID"], item["Sold to ID"], item["Ship to ID"], item["Date"], item["Price"]) for item in data_b["price_overrides"]]
        prices_res_b = resolve_monthly_prices(data_b["base_prices"], over_list_b)
        df_calc_b = run_simulation_pipeline(
            data_b["volume_data"], prices_res_b, data_b["base_costs"],
            data_b["base_var_costs"], data_b["base_dist_costs"],
            data_b["plant_currency"], data_b["fx_rates"]
        )

        # Run row-by-row bridge calculations
        df_bridge = calculate_margin_bridge(
            df_calc_a,
            df_calc_b,
            data_a["fx_rates"],
            data_b["fx_rates"]
        )

        # Aggregate Summary
        summary = summarize_margin_bridge(df_bridge)

        # Breakdown by Material
        df_mat = (
            df_bridge.groupby(["Material", "Material ID"])[
                ["Vol_A", "Vol_B", "VCM_USD_A", "VCM_USD_B", "Volume_Effect", "Price_Effect", "Cost_Effect", "FX_Effect"]
            ]
            .sum()
            .reset_index()
        )
        # Sort by VCM Delta absolute value descending
        df_mat["delta"] = df_mat["VCM_USD_B"] - df_mat["VCM_USD_A"]
        df_mat["abs_delta"] = df_mat["delta"].abs()
        df_mat.sort_values(by="abs_delta", ascending=False, inplace=True)
        df_mat.drop(columns=["abs_delta", "delta"], inplace=True)

        # Breakdown by Month
        df_month = (
            df_bridge.groupby(["Date"])[
                ["Vol_A", "Vol_B", "VCM_USD_A", "VCM_USD_B", "Volume_Effect", "Price_Effect", "Cost_Effect", "FX_Effect"]
            ]
            .sum()
            .reset_index()
        )
        df_month["sort_key"] = df_month["Date"].apply(lambda x: str(x))
        df_month.sort_values(by="sort_key", inplace=True)
        df_month.drop(columns=["sort_key"], inplace=True)

        return {
            "summary": summary,
            "by_material": df_to_records(df_mat),
            "by_month": df_to_records(df_month),
            "raw_preview": df_to_records(df_bridge),
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bridge calculation failed: {str(e)}")


@router.post("/login-log")
def log_user_login(payload: LoginLogInput):
    """Log user access to the backend system for audit purposes."""
    try:
        import datetime
        from pathlib import Path
        
        log_dir = Path("data")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "login_audit.log"
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] User: {payload.name} ({payload.email}) signed in via {payload.provider}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
            
        return {"status": "success", "message": "Login logged successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

