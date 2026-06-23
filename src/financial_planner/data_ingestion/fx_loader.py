"""Loader for monthly FX rates and plant-to-currency mappings."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final, IO

import pandas as pd

from src.financial_planner.data_ingestion.validation import (
    PLANNING_FX_COLUMNS,
    PLANNING_PLANT_CURRENCY_COLUMNS,
    PlanningValidationError,
    run_fx_validation,
    run_plant_currency_validation,
)

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
DEFAULT_RAW_FX_FILE: Final[Path] = PROJECT_ROOT / "data" / "raw" / "mock_fx_rates.csv"
DEFAULT_RAW_PLANT_CURRENCY_FILE: Final[Path] = (
    PROJECT_ROOT / "data" / "raw" / "mock_plant_currency_mapping.csv"
)


def load_fx_data(
    source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_FX_FILE,
) -> pd.DataFrame:
    """Load and validate monthly FX rate records.

    Args:
        source: Path or file-like object containing FX rates CSV.

    Returns:
        A validated pandas DataFrame containing:
            - 'Period': parsed monthly pd.Period.
            - 'Currency': string currency code (e.g. 'EUR').
            - 'Rate': Decimal exchange rate (Units of currency per 1 USD).
    """
    fx_data = pd.read_csv(source, dtype=str)

    report = run_fx_validation(fx_data)
    if not report.is_valid:
        raise PlanningValidationError(report)

    # Convert types for calculation safety
    fx_data = fx_data[PLANNING_FX_COLUMNS].copy()
    fx_data["Date"] = fx_data["Period"].apply(lambda p: pd.Period(p, freq="M"))
    fx_data["Rate"] = fx_data["Rate"].apply(Decimal)

    return fx_data


def load_plant_currency_data(
    source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_PLANT_CURRENCY_FILE,
) -> pd.DataFrame:
    """Load and validate Plant Currency mapping records.

    Args:
        source: Path or file-like object containing Plant Currency mapping CSV.

    Returns:
        A validated pandas DataFrame containing:
            - 'Plant': string plant identifier (e.g. 'PLANT-01').
            - 'Currency': string currency code (e.g. 'EUR').
    """
    mapping_data = pd.read_csv(source, dtype=str)

    report = run_plant_currency_validation(mapping_data)
    if not report.is_valid:
        raise PlanningValidationError(report)

    # Clean strings
    mapping_data = mapping_data[PLANNING_PLANT_CURRENCY_COLUMNS].copy()
    mapping_data["Plant"] = mapping_data["Plant"].astype(str).str.strip()
    mapping_data["Currency"] = mapping_data["Currency"].astype(str).str.strip()

    return mapping_data
