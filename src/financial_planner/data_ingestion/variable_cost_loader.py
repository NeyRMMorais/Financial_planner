"""Planning annual variable cost data loader.

This module defines the ingestion contract and data loading for the
material-specific annual variable production cost records.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final, IO

import pandas as pd

from src.financial_planner.data_ingestion.validation import (
    PLANNING_VARIABLE_COST_COLUMNS,
    PlanningValidationError,
    run_variable_cost_validation,
)
from src.financial_planner.paths import RAW_DIR

DEFAULT_RAW_VAR_COST_FILE: Final[Path] = RAW_DIR / "mock_variable_cost_input.csv"


def load_variable_cost_data(
    source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_VAR_COST_FILE,
) -> pd.DataFrame:
    """Load and validate annual variable cost records.

    Args:
        source: Path or file-like object containing raw annual variable cost CSV data.

    Returns:
        A validated pandas DataFrame containing annual variable costs, with:
            - 'Variable Cost': Decimal unit variable cost.
    """

    cost_data = pd.read_csv(source, dtype=str)

    report = run_variable_cost_validation(cost_data)
    if not report.is_valid:
        raise PlanningValidationError(report)

    # Convert types for calculation safety
    cost_data = cost_data[PLANNING_VARIABLE_COST_COLUMNS].copy()
    cost_data["Variable Cost"] = cost_data["Variable Cost"].apply(Decimal)

    return cost_data
