"""Scenario manager for the financial planner.

Handles listing, loading, saving, cloning, and diffing scenarios.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Final

import pandas as pd

from src.financial_planner.data_ingestion.cost_loader import load_cost_data
from src.financial_planner.data_ingestion.data_loader import load_planning_volume_data
from src.financial_planner.data_ingestion.distribution_cost_loader import load_distribution_cost_data
from src.financial_planner.data_ingestion.fx_loader import load_fx_data, load_plant_currency_data
from src.financial_planner.data_ingestion.price_loader import load_pricing_data
from src.financial_planner.data_ingestion.variable_cost_loader import load_variable_cost_data
from src.financial_planner.paths import RAW_DIR, SCENARIOS_DIR


# Mappings of filenames inside a scenario directory
FILE_MAP: Final[dict[str, str]] = {
    "volume_data": "volume_data.csv",
    "base_prices": "base_prices.csv",
    "price_overrides": "price_overrides.json",
    "base_costs": "base_costs.csv",
    "base_var_costs": "base_var_costs.csv",
    "base_dist_costs": "base_dist_costs.csv",
    "fx_rates": "fx_rates.csv",
    "plant_currency": "plant_currency.csv",
}


def ensure_baseline_exists() -> None:
    """Auto-initialize the 'Baseline' scenario if no scenarios exist."""
    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    baseline_dir = SCENARIOS_DIR / "Baseline"
    if not baseline_dir.exists():
        baseline_dir.mkdir(parents=True, exist_ok=True)

        # Copy raw mock files if they exist
        raw_mappings = {
            "mock_volume_input.csv": "volume_data.csv",
            "mock_price_input.csv": "base_prices.csv",
            "mock_cost_input.csv": "base_costs.csv",
            "mock_variable_cost_input.csv": "base_var_costs.csv",
            "mock_distribution_cost_input.csv": "base_dist_costs.csv",
            "mock_fx_rates.csv": "fx_rates.csv",
            "mock_plant_currency_mapping.csv": "plant_currency.csv",
        }

        for raw_name, scen_name in raw_mappings.items():
            raw_path = RAW_DIR / raw_name
            if raw_path.exists():
                shutil.copy2(raw_path, baseline_dir / scen_name)

        # Create empty price overrides
        with open(baseline_dir / "price_overrides.json", "w", encoding="utf-8") as f:
            json.dump([], f)

        # Write metadata.json
        metadata = {
            "name": "Baseline",
            "created_at": datetime.now().isoformat(),
            "base_scenario": None,
            "description": "Baseline scenario initialized from mock raw data.",
            "change_log": [],
        }
        with open(baseline_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)


def list_scenarios() -> list[dict]:
    """List all available scenarios sorted by creation time."""
    ensure_baseline_exists()
    scenarios = []
    for path in SCENARIOS_DIR.iterdir():
        if path.is_dir():
            meta_path = path / "metadata.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    scenarios.append(meta)
                except Exception:
                    pass
    # Sort by created_at timestamp
    scenarios.sort(key=lambda x: x.get("created_at", ""))
    return scenarios


def create_scenario(name: str, base_scenario: str | None = None, description: str = "") -> dict:
    """Create a new scenario folder and clone base files if requested.

    Args:
        name: Name of the scenario (will be sanitized for folder creation).
        base_scenario: Name of the scenario to clone from.
        description: User notes for the scenario.
    """
    ensure_baseline_exists()
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_", " ")).strip()
    if not safe_name:
        raise ValueError("Scenario name contains invalid characters.")

    target_dir = SCENARIOS_DIR / safe_name
    if target_dir.exists():
        raise ValueError(f"Scenario '{safe_name}' already exists.")

    target_dir.mkdir(parents=True, exist_ok=True)

    if base_scenario:
        base_dir = SCENARIOS_DIR / base_scenario
        if base_dir.exists():
            for file_path in base_dir.iterdir():
                if file_path.is_file() and file_path.name != "metadata.json":
                    shutil.copy2(file_path, target_dir / file_path.name)

    metadata = {
        "name": safe_name,
        "created_at": datetime.now().isoformat(),
        "base_scenario": base_scenario,
        "description": description,
        "change_log": [],
    }

    # Ensure price overrides exists if starting from scratch
    if not base_scenario or not (target_dir / "price_overrides.json").exists():
        with open(target_dir / "price_overrides.json", "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def load_scenario_data(name: str) -> dict:
    """Load and format all input dataframes and price overrides for a scenario."""
    scen_dir = SCENARIOS_DIR / name
    if not scen_dir.exists():
        raise ValueError(f"Scenario '{name}' does not exist.")

    data = {
        "volume_data": None,
        "base_prices": None,
        "price_overrides": [],
        "base_costs": None,
        "base_var_costs": None,
        "base_dist_costs": None,
        "fx_rates": None,
        "plant_currency": None,
    }

    # 1. Volume
    vol_path = scen_dir / FILE_MAP["volume_data"]
    if vol_path.exists():
        data["volume_data"] = load_planning_volume_data(vol_path)

    # 2. Base Prices
    price_path = scen_dir / FILE_MAP["base_prices"]
    if price_path.exists():
        data["base_prices"] = load_pricing_data(price_path)

    # 3. Price Overrides
    over_path = scen_dir / FILE_MAP["price_overrides"]
    if over_path.exists():
        try:
            with open(over_path, "r", encoding="utf-8") as f:
                raw_overrides = json.load(f)
            # Standardize overrides structure (convert Price values to Decimal)
            data["price_overrides"] = []
            for item in raw_overrides:
                data["price_overrides"].append({
                    "Material ID": str(item.get("Material ID", "")).strip(),
                    "Sold to ID": str(item.get("Sold to ID", "")).strip(),
                    "Ship to ID": str(item.get("Ship to ID", "")).strip(),
                    "Date": pd.Period(item.get("Date"), freq="M") if item.get("Date") else None,
                    "Price": Decimal(str(item.get("Price", "0.00"))),
                })
        except Exception:
            data["price_overrides"] = []

    # 4. Base Costs (RM)
    costs_path = scen_dir / FILE_MAP["base_costs"]
    if costs_path.exists():
        data["base_costs"] = load_cost_data(costs_path)

    # 5. Variable Costs
    var_path = scen_dir / FILE_MAP["base_var_costs"]
    if var_path.exists():
        data["base_var_costs"] = load_variable_cost_data(var_path)

    # 6. Distribution Costs
    dist_path = scen_dir / FILE_MAP["base_dist_costs"]
    if dist_path.exists():
        data["base_dist_costs"] = load_distribution_cost_data(dist_path)

    # 7. FX Rates
    fx_path = scen_dir / FILE_MAP["fx_rates"]
    if fx_path.exists():
        data["fx_rates"] = load_fx_data(fx_path)

    # 8. Plant Currency Mapping
    pc_path = scen_dir / FILE_MAP["plant_currency"]
    if pc_path.exists():
        data["plant_currency"] = load_plant_currency_data(pc_path)

    return data


def save_scenario_data(name: str, data_dict: dict) -> None:
    """Save all dataframes and overrides back to the scenario folder on disk."""
    scen_dir = SCENARIOS_DIR / name
    if not scen_dir.exists():
        raise ValueError(f"Scenario '{name}' does not exist.")

    # 1. Save dataframes
    for key, filename in FILE_MAP.items():
        if key == "price_overrides":
            continue
        df = data_dict.get(key)
        if df is not None:
            df_to_save = df.copy()
            for col in df_to_save.columns:
                if df_to_save[col].dtype == object:
                    df_to_save[col] = df_to_save[col].apply(
                        lambda val: str(val) if isinstance(val, pd.Period) else val
                    )
            df_to_save.to_csv(scen_dir / filename, index=False)

    # 2. Save price overrides JSON
    overrides = data_dict.get("price_overrides", [])
    serializable_overrides = []
    for item in overrides:
        serializable_overrides.append({
            "Material ID": item.get("Material ID"),
            "Sold to ID": item.get("Sold to ID"),
            "Ship to ID": item.get("Ship to ID"),
            "Date": str(item.get("Date")) if item.get("Date") else None,
            "Price": float(item.get("Price")) if isinstance(item.get("Price"), Decimal) else item.get("Price"),
        })
    with open(scen_dir / FILE_MAP["price_overrides"], "w", encoding="utf-8") as f:
        json.dump(serializable_overrides, f, indent=2)

    # 3. Read metadata to check for parent base scenario to build auto change log
    meta_path = scen_dir / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}
    else:
        meta = {}

    meta["name"] = name
    # Compute auto-generated change log
    base_scen_name = meta.get("base_scenario")
    if base_scen_name:
        meta["change_log"] = diff_scenarios_inputs(base_scen_name, name)
    else:
        meta["change_log"] = ["Initialized from scratch (no base scenario)."]

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def diff_dataframe(
    df_base: pd.DataFrame | None,
    df_new: pd.DataFrame | None,
    keys: list[str],
    value_cols: list[str],
) -> list[str]:
    """Helper to perform outer joins and list difference details between two input dfs."""
    logs = []
    if df_base is None and df_new is None:
        return logs
    if df_base is None:
        logs.append("Data added (did not exist in base scenario).")
        return logs
    if df_new is None:
        logs.append("Data cleared/removed.")
        return logs

    # Standardize string representations of keys
    b_df = df_base.copy()
    n_df = df_new.copy()

    for col in keys:
        if col in b_df.columns:
            b_df[col] = b_df[col].astype(str).str.strip()
        if col in n_df.columns:
            n_df[col] = n_df[col].astype(str).str.strip()

    # Deduplicate before outer merge to avoid merge explosions
    b_df = b_df.drop_duplicates(subset=keys)
    n_df = n_df.drop_duplicates(subset=keys)

    # Outer join
    merged = pd.merge(
        b_df,
        n_df,
        on=keys,
        how="outer",
        suffixes=("_base", "_new"),
    )

    # 1. Added
    added_mask = merged[value_cols[0] + "_base"].isna() & merged[value_cols[0] + "_new"].notna()
    added_count = added_mask.sum()
    if added_count > 0:
        logs.append(f"{added_count} rows added.")

    # 2. Deleted
    deleted_mask = merged[value_cols[0] + "_new"].isna() & merged[value_cols[0] + "_base"].notna()
    deleted_count = deleted_mask.sum()
    if deleted_count > 0:
        logs.append(f"{deleted_count} rows deleted.")

    # 3. Modified
    modified_count = 0
    common_mask = merged[value_cols[0] + "_base"].notna() & merged[value_cols[0] + "_new"].notna()
    for col in value_cols:
        col_base = col + "_base"
        col_new = col + "_new"
        diff_mask = common_mask & (merged[col_base] != merged[col_new])
        modified_count += diff_mask.sum()

    if modified_count > 0:
        logs.append(f"{modified_count} values updated/modified.")

    return logs


def diff_scenarios_inputs(scenario_base: str, scenario_new: str) -> list[str]:
    """Generate a detailed change log comparing the inputs of two scenarios."""
    logs = []
    base_dir = SCENARIOS_DIR / scenario_base
    new_dir = SCENARIOS_DIR / scenario_new

    if not base_dir.exists() or not new_dir.exists():
        return ["Unable to compare: scenario directories missing."]

    try:
        base_data = load_scenario_data(scenario_base)
        new_data = load_scenario_data(scenario_new)
    except Exception as e:
        return [f"Error loading scenarios for diff: {e}"]

    configs = [
        ("volume_data", ["Material ID", "Plant", "Sold to ID", "Ship to ID", "Date"], ["Volume"]),
        ("base_prices", ["Sold to ID", "Ship to ID", "Material ID"], ["Price"]),
        ("base_costs", ["Plant", "Material ID", "Date"], ["Cost"]),
        ("base_var_costs", ["Material ID"], ["Variable Cost"]),
        ("base_dist_costs", ["Ship to ID"], ["Distribution Cost"]),
        ("fx_rates", ["Period", "Currency"], ["Rate"]),
        ("plant_currency", ["Plant"], ["Currency"]),
    ]

    for key, keys, val_cols in configs:
        df_base = base_data.get(key)
        df_new = new_data.get(key)
        diff_logs = diff_dataframe(df_base, df_new, keys, val_cols)
        if diff_logs:
            file_label = key.replace("_", " ").title()
            logs.append(f"**{file_label}**: " + ", ".join(diff_logs))

    # Compare Price Overrides (JSON list converted to dataframes)
    over_base = base_data.get("price_overrides", [])
    over_new = new_data.get("price_overrides", [])

    if over_base or over_new:
        df_over_base = pd.DataFrame(over_base) if over_base else pd.DataFrame(columns=["Material ID", "Sold to ID", "Ship to ID", "Date", "Price"])
        df_over_new = pd.DataFrame(over_new) if over_new else pd.DataFrame(columns=["Material ID", "Sold to ID", "Ship to ID", "Date", "Price"])
        
        over_keys = ["Material ID", "Sold to ID", "Ship to ID", "Date"]
        diff_logs = diff_dataframe(df_over_base, df_over_new, over_keys, ["Price"])
        if diff_logs:
            logs.append("**Price Overrides**: " + ", ".join(diff_logs))

    if not logs:
        logs.append("No changes detected in any input files.")

    return logs


def apply_scenario_drivers(
    name: str,
    adjustments: list[dict],
    description: str | None = None,
    author: str = "User",
) -> dict:
    """Apply macro and commercial driver adjustments to a scenario with top-down atomic cascading.

    Args:
        name: Target scenario name.
        adjustments: List of adjustments with keys 'driver_type', 'scope_type', 'scope_value', 'adjustment_type', 'value'.
        description: Optional user note.
        author: User name or email.

    Returns:
        dict containing the applied result, new metrics, and structured change log entry.
    """
    import uuid
    from src.financial_planner.calculations.bridge import get_product_line
    from src.financial_planner.calculations.pipeline import run_simulation_pipeline, generate_summary_metrics

    scen_dir = SCENARIOS_DIR / name
    if not scen_dir.exists():
        raise ValueError(f"Scenario '{name}' does not exist.")

    # 1. Load initial scenario data and compute baseline VCM
    data = load_scenario_data(name)
    try:
        from src.financial_planner.calculations.pricing import PriceOverride, resolve_monthly_prices
        over_list = [PriceOverride(item["Material ID"], item["Sold to ID"], item["Ship to ID"], item["Date"], item["Price"]) for item in data.get("price_overrides", [])]
        prices_res = resolve_monthly_prices(data["base_prices"], over_list)
        init_calc = run_simulation_pipeline(
            data["volume_data"],
            prices_res,
            data["base_costs"],
            data["base_var_costs"],
            data["base_dist_costs"],
            data["plant_currency"],
            data["fx_rates"],
        )
        init_metrics = generate_summary_metrics(init_calc)
        vcm_before_usd = init_metrics["total_vcm_usd"]
    except Exception:
        vcm_before_usd = Decimal("0.00")

    # 2. Iterate and apply each adjustment to the atomic datasets
    applied_descriptions = []
    primary_driver = "Multi-Driver"

    for adj in adjustments:
        driver_type = str(adj.get("driver_type", "")).lower().strip()
        scope_type = str(adj.get("scope_type", "portfolio")).lower().strip()
        scope_val = adj.get("scope_value")
        scope_val_str = str(scope_val).strip() if scope_val is not None else ""
        adj_type = str(adj.get("adjustment_type", "pct")).lower().strip()
        val = Decimal(str(adj.get("value", "0.0")))

        # --- A. VOLUME DRIVER ---
        if driver_type == "volume" and data["volume_data"] is not None:
            primary_driver = "Volume"
            df = data["volume_data"].copy()

            def match_vol(row):
                if scope_type == "product_line":
                    return get_product_line(row.get("Material ID"), row.get("Material")) == scope_val_str
                elif scope_type == "material":
                    return str(row.get("Material ID", "")).strip() == scope_val_str or str(row.get("Material", "")).strip() == scope_val_str
                elif scope_type == "customer":
                    return str(row.get("Sold to ID", "")).strip() == scope_val_str or str(row.get("Sold to", "")).strip() == scope_val_str
                elif scope_type == "plant":
                    return str(row.get("Plant", "")).strip() == scope_val_str
                return True  # portfolio

            mask = df.apply(match_vol, axis=1)
            if adj_type == "pct":
                multiplier = Decimal("1.0") + (val / Decimal("100.0"))
                df.loc[mask, "Volume"] = df.loc[mask, "Volume"].apply(lambda v: max(Decimal("0.000"), Decimal(str(v)) * multiplier))
                applied_descriptions.append(f"Volume {val:+}% on {scope_type} ({scope_val_str or 'All'})")
            elif adj_type == "delta":
                df.loc[mask, "Volume"] = df.loc[mask, "Volume"].apply(lambda v: max(Decimal("0.000"), Decimal(str(v)) + val))
                applied_descriptions.append(f"Volume {val:+} MT on {scope_type} ({scope_val_str or 'All'})")

            data["volume_data"] = df

        # --- B. PRICE DRIVER ---
        elif driver_type == "price" and data["base_prices"] is not None:
            primary_driver = "Price"
            df = data["base_prices"].copy()

            def match_price(row):
                if scope_type == "product_line":
                    return get_product_line(row.get("Material ID"), "") == scope_val_str
                elif scope_type == "material":
                    return str(row.get("Material ID", "")).strip() == scope_val_str
                elif scope_type == "customer":
                    return str(row.get("Sold to ID", "")).strip() == scope_val_str
                return True

            mask = df.apply(match_price, axis=1)
            if adj_type == "pct":
                multiplier = Decimal("1.0") + (val / Decimal("100.0"))
                df.loc[mask, "Price"] = df.loc[mask, "Price"].apply(lambda p: max(Decimal("0.00"), Decimal(str(p)) * multiplier))
                applied_descriptions.append(f"Price {val:+}% on {scope_type} ({scope_val_str or 'All'})")
            elif adj_type == "delta":
                df.loc[mask, "Price"] = df.loc[mask, "Price"].apply(lambda p: max(Decimal("0.00"), Decimal(str(p)) + val))
                applied_descriptions.append(f"Price {val:+} on {scope_type} ({scope_val_str or 'All'})")

            data["base_prices"] = df

        # --- C. RAW MATERIAL COST DRIVER ---
        elif driver_type in ("raw_cost", "raw_material_cost", "feedstock") and data["base_costs"] is not None:
            primary_driver = "Raw Material Cost"
            df = data["base_costs"].copy()

            def match_cost(row):
                if scope_type == "product_line":
                    return get_product_line(row.get("Material ID"), "") == scope_val_str
                elif scope_type == "material":
                    return str(row.get("Material ID", "")).strip() == scope_val_str
                elif scope_type == "plant":
                    return str(row.get("Plant", "")).strip() == scope_val_str
                return True

            mask = df.apply(match_cost, axis=1)
            if adj_type == "pct":
                multiplier = Decimal("1.0") + (val / Decimal("100.0"))
                df.loc[mask, "Cost"] = df.loc[mask, "Cost"].apply(lambda c: max(Decimal("0.00"), Decimal(str(c)) * multiplier))
                applied_descriptions.append(f"Raw Mat Cost {val:+}% on {scope_type} ({scope_val_str or 'All'})")
            elif adj_type == "delta":
                df.loc[mask, "Cost"] = df.loc[mask, "Cost"].apply(lambda c: max(Decimal("0.00"), Decimal(str(c)) + val))
                applied_descriptions.append(f"Raw Mat Cost {val:+} on {scope_type} ({scope_val_str or 'All'})")

            data["base_costs"] = df

        # --- D. VARIABLE NON-RAW COST DRIVER ---
        elif driver_type in ("var_cost", "variable_cost") and data["base_var_costs"] is not None:
            primary_driver = "Variable Cost"
            df = data["base_var_costs"].copy()

            def match_var(row):
                if scope_type == "product_line":
                    return get_product_line(row.get("Material ID"), row.get("Material")) == scope_val_str
                elif scope_type == "material":
                    return str(row.get("Material ID", "")).strip() == scope_val_str or str(row.get("Material", "")).strip() == scope_val_str
                return True

            mask = df.apply(match_var, axis=1)
            if adj_type == "pct":
                multiplier = Decimal("1.0") + (val / Decimal("100.0"))
                df.loc[mask, "Variable Cost"] = df.loc[mask, "Variable Cost"].apply(lambda c: max(Decimal("0.00"), Decimal(str(c)) * multiplier))
                applied_descriptions.append(f"Variable Cost {val:+}% on {scope_type} ({scope_val_str or 'All'})")
            elif adj_type == "delta":
                df.loc[mask, "Variable Cost"] = df.loc[mask, "Variable Cost"].apply(lambda c: max(Decimal("0.00"), Decimal(str(c)) + val))
                applied_descriptions.append(f"Variable Cost {val:+} on {scope_type} ({scope_val_str or 'All'})")

            data["base_var_costs"] = df

        # --- E. DISTRIBUTION COST DRIVER ---
        elif driver_type in ("dist_cost", "distribution_cost", "freight") and data["base_dist_costs"] is not None:
            primary_driver = "Distribution Cost"
            df = data["base_dist_costs"].copy()

            def match_dist(row):
                if scope_type == "customer":
                    return scope_val_str in str(row.get("Ship to ID", "")) or scope_val_str in str(row.get("Ship to", ""))
                return True

            mask = df.apply(match_dist, axis=1)
            if adj_type == "pct":
                multiplier = Decimal("1.0") + (val / Decimal("100.0"))
                df.loc[mask, "Distribution Cost"] = df.loc[mask, "Distribution Cost"].apply(lambda c: max(Decimal("0.00"), Decimal(str(c)) * multiplier))
                applied_descriptions.append(f"Distribution Cost {val:+}% on {scope_type} ({scope_val_str or 'All'})")
            elif adj_type == "delta":
                df.loc[mask, "Distribution Cost"] = df.loc[mask, "Distribution Cost"].apply(lambda c: max(Decimal("0.00"), Decimal(str(c)) + val))
                applied_descriptions.append(f"Distribution Cost {val:+} on {scope_type} ({scope_val_str or 'All'})")

            data["base_dist_costs"] = df

        # --- F. FX RATE DRIVER ---
        elif driver_type in ("fx_rate", "fx") and data["fx_rates"] is not None:
            primary_driver = "FX Rate"
            df = data["fx_rates"].copy()

            def match_fx(row):
                if scope_val_str:
                    return str(row.get("Currency", "")).strip().upper() == scope_val_str.upper()
                return True

            mask = df.apply(match_fx, axis=1)
            if adj_type == "absolute":
                df.loc[mask, "Rate"] = val
                applied_descriptions.append(f"FX Rate {scope_val_str} set to {val}")
            elif adj_type == "pct":
                multiplier = Decimal("1.0") + (val / Decimal("100.0"))
                df.loc[mask, "Rate"] = df.loc[mask, "Rate"].apply(lambda r: Decimal(str(r)) * multiplier)
                applied_descriptions.append(f"FX Rate {scope_val_str} {val:+}%")

            data["fx_rates"] = df

    # 3. Save all modified datasets back to disk
    save_scenario_data(name, data)

    # 4. Re-calculate new metrics to determine exact financial impact
    from src.financial_planner.calculations.pricing import PriceOverride, resolve_monthly_prices
    over_list = [PriceOverride(item["Material ID"], item["Sold to ID"], item["Ship to ID"], item["Date"], item["Price"]) for item in data.get("price_overrides", [])]
    prices_res = resolve_monthly_prices(data["base_prices"], over_list)
    new_calc = run_simulation_pipeline(
        data["volume_data"],
        prices_res,
        data["base_costs"],
        data["base_var_costs"],
        data["base_dist_costs"],
        data["plant_currency"],
        data["fx_rates"],
    )
    new_metrics = generate_summary_metrics(new_calc)
    vcm_after_usd = new_metrics["total_vcm_usd"]

    impact_usd = vcm_after_usd - vcm_before_usd
    impact_pct = ((impact_usd / vcm_before_usd) * Decimal("100.0")) if vcm_before_usd != Decimal("0.00") else Decimal("0.00")

    # 5. Build structured change log entry
    summary_desc = description or "; ".join(applied_descriptions) or "Macro driver adjustment applied"
    serialized_adjustments = []
    for adj in adjustments:
        serialized_adjustments.append({
            "driver_type": adj.get("driver_type"),
            "scope_type": adj.get("scope_type"),
            "scope_value": adj.get("scope_value"),
            "adjustment_type": adj.get("adjustment_type"),
            "value": float(adj["value"]) if isinstance(adj.get("value"), Decimal) else adj.get("value"),
        })

    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "author": author,
        "driver": primary_driver,
        "description": summary_desc,
        "scope": {"adjustments": serialized_adjustments},
        "vcm_before_usd": str(vcm_before_usd),
        "vcm_after_usd": str(vcm_after_usd),
        "impact_usd": str(impact_usd),
        "impact_pct": f"{impact_pct:+.2f}%",
    }

    # 6. Update metadata.json with structured impact trail
    meta_path = scen_dir / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}
    else:
        meta = {}

    if "impact_trail" not in meta:
        meta["impact_trail"] = []
    meta["impact_trail"].insert(0, entry)

    # Also prepend human-readable bullet to change_log
    log_bullet = f"[{entry['timestamp'][:10]}] {summary_desc} -> Impact: {impact_usd:+,.2f} USD ({impact_pct:+.2f}%)"
    if "change_log" not in meta or not isinstance(meta["change_log"], list):
        meta["change_log"] = []
    meta["change_log"].insert(0, log_bullet)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    return {
        "scenario": name,
        "applied_count": len(adjustments),
        "change_log_entry": entry,
        "new_metrics": new_metrics,
    }

