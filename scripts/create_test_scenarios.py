"""Script to organize mock assumption files into categorized folders under data/raw/ and create baseline, update, and incomplete versions for testing."""

import os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Define raw input source filenames
SOURCES = {
    "volume_data": "mock_volume_input.csv",
    "base_prices": "mock_price_input.csv",
    "base_costs": "mock_cost_input.csv",
    "base_var_costs": "mock_variable_cost_input.csv",
    "base_dist_costs": "mock_distribution_cost_input.csv",
    "fx_rates": "mock_fx_rates.csv",
    "plant_currency": "mock_plant_currency_mapping.csv",
}

def main():
    print(f"RAW_DIR path: {RAW_DIR}")
    if not RAW_DIR.exists():
        print("Raw data directory does not exist.")
        return

    for key, filename in SOURCES.items():
        src_path = RAW_DIR / filename
        if not src_path.exists():
            print(f"Warning: Source file {src_path} not found. Skipping...")
            continue

        # Create target subfolder by assumption type
        dest_folder = RAW_DIR / key
        dest_folder.mkdir(parents=True, exist_ok=True)
        print(f"\nOrganizing assumption: '{key}' under {dest_folder.relative_to(PROJECT_ROOT)}")

        # Read base dataframe
        df = pd.read_csv(src_path)

        # Define file prefix based on the assumption key
        prefix = key.replace("base_", "")
        if prefix == "volume_data":
            prefix = "volume"

        # ----------------------------------------------------
        # 1. BASELINE VERSION
        # ----------------------------------------------------
        baseline_path = dest_folder / f"{prefix}_baseline.csv"
        df.to_csv(baseline_path, index=False)
        print(f" - Created {prefix}_baseline.csv ({len(df)} rows)")

        # ----------------------------------------------------
        # 2. UPDATE VERSION (Simulates incremental edits)
        # ----------------------------------------------------
        update_path = dest_folder / f"{prefix}_update.csv"
        df_update = df.copy()

        if key == "volume_data":
            # Increase volume by 10% for PLANT-01
            mask = df_update["Plant"] == "PLANT-01"
            df_update.loc[mask, "Volume"] = (df_update.loc[mask, "Volume"] * 1.1).round(3)
        elif key == "base_prices":
            # Increase prices by 10%
            df_update["Price"] = (df_update["Price"] * 1.1).round(2)
        elif key == "base_costs":
            # Increase RM costs by 5.0
            df_update["Cost"] = (df_update["Cost"] + 5.0).round(3)
        elif key == "base_var_costs":
            # Increase variable costs by 1.50
            df_update["Variable Cost"] = (df_update["Variable Cost"] + 1.50).round(2)
        elif key == "base_dist_costs":
            # Increase distribution costs by 2.0
            df_update["Distribution Cost"] = (df_update["Distribution Cost"] + 2.0).round(2)
        elif key == "fx_rates":
            # Update EUR rates (e.g. 0.92 -> 0.88)
            eur_mask = df_update["Currency"] == "EUR"
            df_update.loc[eur_mask, "Rate"] = 0.88
        elif key == "plant_currency":
            # Change PLANT-06 local currency from EUR to USD
            p6_mask = df_update["Plant"] == "PLANT-06"
            df_update.loc[p6_mask, "Currency"] = "USD"

        df_update.to_csv(update_path, index=False)
        print(f" - Created {prefix}_update.csv ({len(df_update)} rows)")

        # ----------------------------------------------------
        # 3. INCOMPLETE ERROR VERSION (Simulates incomplete mappings / errors)
        # ----------------------------------------------------
        incomplete_path = dest_folder / f"{prefix}_incomplete_error.csv"
        df_inc = df.copy()

        if key == "volume_data":
            # Introduce an unmapped Material ID and unmapped Ship to ID
            # This triggers price & distribution completeness check errors.
            df_inc.loc[0, "Material ID"] = "MAT-9999"
            df_inc.loc[1, "Ship to ID"] = "SHIP-999-NL"
        elif key == "base_prices":
            # Delete prices for CUST-001 (creates pricing gaps)
            df_inc = df_inc[df_inc["Sold to ID"] != "CUST-001"]
        elif key == "base_costs":
            # Delete raw material costs for period 2026-12 (creates monthly cost gaps)
            df_inc = df_inc[df_inc["Period"] != "2026-12"]
        elif key == "base_var_costs":
            # Delete variable costs mapping for MAT-1001 (creates variable cost gaps)
            df_inc = df_inc[df_inc["Material ID"] != "MAT-1001"]
        elif key == "base_dist_costs":
            # Delete distribution cost for SHIP-001-NL (creates distribution cost gaps)
            df_inc = df_inc[df_inc["Ship to ID"] != "SHIP-001-NL"]
        elif key == "fx_rates":
            # Delete EUR rates for 2026-12 (creates currency conversion FX gaps)
            df_inc = df_inc[~((df_inc["Period"] == "2026-12") & (df_inc["Currency"] == "EUR"))]
        elif key == "plant_currency":
            # Delete PLANT-01 mapping (creates plant currency gaps)
            df_inc = df_inc[df_inc["Plant"] != "PLANT-01"]

        df_inc.to_csv(incomplete_path, index=False)
        print(f" - Created {prefix}_incomplete_error.csv ({len(df_inc)} rows)")

    print("\nSuccessfully organized all scenarios variations under categorized subfolders!")

if __name__ == "__main__":
    main()
