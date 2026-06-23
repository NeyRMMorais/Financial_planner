"""Loader for annual distribution costs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
import pandas as pd

from src.financial_planner.data_ingestion.validation import (
    run_dist_cost_validation,
    PlanningValidationError,
)


def load_distribution_cost_data(source: Any) -> pd.DataFrame:
    """
    Load annual distribution costs from a CSV source, applying strict validation.

    Args:
        source: File path, buffer, or any object accepted by pd.read_csv.

    Returns:
        A validated pandas DataFrame containing annual distribution cost records.
        The 'Distribution Cost' column will be typed as Decimal.

    Raises:
        PlanningValidationError: If the dataset violates financial planning rules.
    """
    df = pd.read_csv(source, dtype=str)

    # 1. Run schema and validation rules against the raw string data
    report = run_dist_cost_validation(df)
    if not report.is_valid:
        raise PlanningValidationError(report)

    # 2. Type conversions for valid data
    # Strip whitespace to prevent hidden mismatches
    df["Ship to"] = df["Ship to"].str.strip()
    df["Ship to ID"] = df["Ship to ID"].str.strip()

    # Convert Distribution Cost to exact Decimal
    df["Distribution Cost"] = df["Distribution Cost"].apply(
        lambda x: Decimal(str(x).strip())
    )

    return df
