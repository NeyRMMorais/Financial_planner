"""Script to wipe all active scenarios and move initial raw mock files to a backup folder, starting the app with a clean slate."""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_BACKUP_DIR = PROJECT_ROOT / "data" / "raw_backup"
SCENARIOS_DIR = PROJECT_ROOT / "data" / "scenarios"

def main():
    # 1. Back up loose mock CSV files from data/raw/
    RAW_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Backup directory: {RAW_BACKUP_DIR}")

    loose_mock_files = [
        "mock_volume_input.csv",
        "mock_price_input.csv",
        "mock_cost_input.csv",
        "mock_variable_cost_input.csv",
        "mock_distribution_cost_input.csv",
        "mock_fx_rates.csv",
        "mock_plant_currency_mapping.csv",
        "mock_price_input_increased_10pct.csv",
        "mock_price_input_missing.csv"
    ]

    for filename in loose_mock_files:
        src = RAW_DIR / filename
        if src.exists():
            dest = RAW_BACKUP_DIR / filename
            shutil.move(src, dest)
            print(f"Backed up: {filename} -> data/raw_backup/")

    # 2. Delete all folders under data/scenarios/
    if SCENARIOS_DIR.exists():
        for path in SCENARIOS_DIR.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Deleted scenario directory: {path.name}")
    
    print("\nSuccessfully cleared scenarios and initial loose mock files!")

if __name__ == "__main__":
    main()
