"""Planning monthly raw material cost data loader.

This module defines the ingestion contract and data loading for the
plant-specific product monthly raw material cost records.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final, IO

import pandas as pd

from src.financial_planner.data_ingestion.validation import (
    PLANNING_COST_COLUMNS,
    PlanningValidationError,
    run_cost_validation,
)
from src.financial_planner.paths import RAW_DIR

DEFAULT_RAW_COST_FILE: Final[Path] = RAW_DIR / "mock_cost_input.csv"


def load_cost_data(
    source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_COST_FILE,
) -> pd.DataFrame:
    """Load and validate monthly raw material cost records.

    Args:
        source: Path or file-like object containing raw monthly RM cost CSV data.

    Returns:
        A validated pandas DataFrame containing monthly RM costs, with:
            - 'Date': parsed monthly pd.Period.
            - 'Cost': Decimal unit cost.
    """

    cost_data = pd.read_csv(source, dtype=str)

    report = run_cost_validation(cost_data)
    if not report.is_valid:
        raise PlanningValidationError(report)

    # Convert types for calculation safety
    cost_data = cost_data[PLANNING_COST_COLUMNS].copy()
    cost_data["Date"] = cost_data["Period"].apply(lambda p: pd.Period(p, freq="M"))
    cost_data["Cost"] = cost_data["Cost"].apply(Decimal)

    return cost_data
