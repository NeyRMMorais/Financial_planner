"""Planning pricing data loader.

This module defines the ingestion contract and data loading for the
customer-specific product pricing records.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final, IO

import pandas as pd

from src.financial_planner.data_ingestion.validation import (
    PLANNING_PRICE_COLUMNS,
    PlanningValidationError,
    run_pricing_validation,
)
from src.financial_planner.paths import RAW_DIR

DEFAULT_RAW_PRICE_FILE: Final[Path] = RAW_DIR / "mock_price_input.csv"


def load_pricing_data(
    source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_PRICE_FILE,
) -> pd.DataFrame:
    """Load and validate customer product pricing records.

    Args:
        source: Path or file-like object containing raw base pricing CSV data.

    Returns:
        A validated pandas DataFrame containing base pricing.
    """

    price_data = pd.read_csv(source, dtype=str)

    report = run_pricing_validation(price_data)
    if not report.is_valid:
        raise PlanningValidationError(report)

    # Standardize copy and convert prices to Decimal
    price_data = price_data[PLANNING_PRICE_COLUMNS].copy()
    price_data["Price"] = price_data["Price"].apply(Decimal)

    return price_data
