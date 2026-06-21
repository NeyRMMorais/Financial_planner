"""Planning volume data loader.

This module defines the first planning input: monthly sales volume by material,
sold-to customer, and ship-to receiving entity. The dataset is intentionally
limited to operational volume fields because price, cost, and margin formulas
will be added in the calculation engine after the ingestion contract is agreed.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final, IO

import pandas as pd

from src.financial_planner.data_ingestion.validation import (
    PlanningValidationError,
    run_advanced_validation,
)


PLANNING_VOLUME_COLUMNS: Final[list[str]] = [
    "Material",
    "Material ID",
    "Date",
    "Sold to ID",
    "Sold to",
    "Ship to ID",
    "Ship to",
    "Plant",
    "Volume",
]

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
DEFAULT_RAW_VOLUME_FILE: Final[Path] = PROJECT_ROOT / "data" / "raw" / "mock_volume_input.csv"


def create_mock_volume_dataset() -> pd.DataFrame:
    """Create a mock monthly volume dataset that starts the planning process.

    Business logic:
        Each row represents planned or actual volume demand for one material,
        sold-to customer, ship-to receiving entity, and calendar month.

    Mathematical treatment:
        Volume is stored as ``Decimal`` tons instead of binary floating-point
        values, preserving exact decimal quantities before later price, cost,
        and margin calculations are applied. Zero-volume rows are allowed
        because they are valid planning signals and must be handled explicitly
        by downstream calculations.

    Returns:
        A pandas DataFrame with the agreed planning volume schema.
    """

    records = [
        {
            "Material": "Premium Resin A",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-01", freq="M"),
            "Sold to ID": "CUST-001",
            "Sold to": "Northstar Manufacturing BV",
            "Ship to ID": "SHIP-001-NL",
            "Ship to": "Northstar Manufacturing BV - Rotterdam Plant",
            "Plant": "PLANT-01",
            "Volume": Decimal("125.500"),
        },
        {
            "Material": "Premium Resin A",
            "Material ID": "MAT-1001",
            "Date": pd.Period("2026-02", freq="M"),
            "Sold to ID": "CUST-001",
            "Sold to": "Northstar Manufacturing BV",
            "Ship to ID": "SHIP-001-NL",
            "Ship to": "Northstar Manufacturing BV - Rotterdam Plant",
            "Plant": "PLANT-01",
            "Volume": Decimal("132.250"),
        },
        {
            "Material": "Industrial Additive B",
            "Material ID": "MAT-2004",
            "Date": pd.Period("2026-01", freq="M"),
            "Sold to ID": "CUST-014",
            "Sold to": "HelioPack GmbH",
            "Ship to ID": "SHIP-014-DE",
            "Ship to": "HelioPack GmbH - Hamburg Site",
            "Plant": "PLANT-02",
            "Volume": Decimal("87.000"),
        },
        {
            "Material": "Industrial Additive B",
            "Material ID": "MAT-2004",
            "Date": pd.Period("2026-02", freq="M"),
            "Sold to ID": "CUST-014",
            "Sold to": "HelioPack GmbH",
            "Ship to ID": "SHIP-014-DE",
            "Ship to": "HelioPack GmbH - Hamburg Site",
            "Plant": "PLANT-02",
            "Volume": Decimal("0.000"),
        },
        {
            "Material": "Specialty Compound C",
            "Material ID": "MAT-3098",
            "Date": pd.Period("2026-01", freq="M"),
            "Sold to ID": "CUST-027",
            "Sold to": "Atlas Components SA",
            "Ship to ID": "SHIP-027-FR",
            "Ship to": "Atlas Components SA - Lyon Warehouse",
            "Plant": "PLANT-03",
            "Volume": Decimal("41.750"),
        },
        {
            "Material": "Specialty Compound C",
            "Material ID": "MAT-3098",
            "Date": pd.Period("2026-02", freq="M"),
            "Sold to ID": "CUST-027",
            "Sold to": "Atlas Components SA",
            "Ship to ID": "SHIP-027-BE",
            "Ship to": "Atlas Components SA - Antwerp DC",
            "Plant": "PLANT-03",
            "Volume": Decimal("46.125"),
        },
    ]

    return pd.DataFrame.from_records(records, columns=PLANNING_VOLUME_COLUMNS)


def load_volume_csv(source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_VOLUME_FILE) -> pd.DataFrame:
    """Load monthly planning volume from a raw CSV source file.

    Business logic:
        The CSV represents the day-to-day source extract that starts the
        planning workflow. Each row is one material/customer/ship-to/month
        volume signal measured in tons.

    Mathematical treatment:
        The ``Volume`` column is read as text and converted to ``Decimal`` so
        downstream financial formulas never inherit binary floating-point
        rounding. The ``Date`` column is converted to a monthly pandas Period to
        make month-level grouping explicit.

    Args:
        source: Path or uploaded file-like object containing raw planning volume CSV.

    Returns:
        A pandas DataFrame with validated planning volume rows.
    """

    volume_data = pd.read_csv(source, dtype=str)
    
    # Run the advanced validation suite on the raw string dataframe
    report = run_advanced_validation(volume_data)
    if not report.is_valid:
        raise PlanningValidationError(report)

    volume_data = volume_data[PLANNING_VOLUME_COLUMNS].copy()
    volume_data["Date"] = volume_data["Date"].apply(lambda value: pd.Period(value, freq="M"))
    volume_data["Volume"] = volume_data["Volume"].apply(Decimal)
    validate_volume_dataset(volume_data)
    return volume_data


def validate_required_values(volume_data: pd.DataFrame) -> None:
    """Validate that all required planning input values are populated.

    Business rule:
        Required values must be present in the source file. Empty strings and
        missing values are both invalid because downstream calculations need to
        distinguish intentional zero volume from incomplete source data.

    Args:
        volume_data: Dataset to inspect for blank or missing required values.

    Raises:
        ValueError: If any required planning fields are missing values.
    """

    null_columns = [
        column
        for column in PLANNING_VOLUME_COLUMNS
        if volume_data[column].isna().any()
        or volume_data[column].astype(str).str.strip().eq("").any()
    ]
    if null_columns:
        raise ValueError(f"Required columns contain missing values: {null_columns}")


def validate_volume_dataset(volume_data: pd.DataFrame) -> None:
    """Validate the minimum schema and data quality rules for volume planning.

    Business rules:
        The planning process requires complete material, customer, ship-to,
        month, and volume values. Missing volume is rejected because downstream
        margin formulas cannot distinguish missing demand from intentional zero
        demand. Zero volume is valid and should be handled by calculation logic
        without divide-by-zero failures.

    Args:
        volume_data: Dataset to validate before planning calculations begin.

    Raises:
        ValueError: If required columns are missing or required values are null.
        TypeError: If any volume value is not a ``Decimal`` instance.
    """

    missing_columns = [
        column for column in PLANNING_VOLUME_COLUMNS if column not in volume_data.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    validate_required_values(volume_data)

    non_decimal_rows = [
        index
        for index, value in volume_data["Volume"].items()
        if not isinstance(value, Decimal)
    ]
    if non_decimal_rows:
        raise TypeError(f"Volume must use Decimal values. Invalid rows: {non_decimal_rows}")


def load_planning_volume_data(
    source: Path | IO[str] | IO[bytes] = DEFAULT_RAW_VOLUME_FILE,
) -> pd.DataFrame:
    """Load and validate planning volume data for the current foundation phase.

    In this foundation version, the source is a raw CSV file stored under
    ``data/raw``. This function acts as the stable ingestion entry point so
    future Excel, database, or enterprise source loaders can be swapped in
    without changing downstream calculation code.

    Returns:
        A validated pandas DataFrame containing monthly volume in tons.
    """

    return load_volume_csv(source)


if __name__ == "__main__":
    dataset = load_planning_volume_data()
    print(dataset)
