import csv
from decimal import Decimal
from io import StringIO
import pytest
import pandas as pd

from src.financial_planner.data_ingestion.distribution_cost_loader import load_distribution_cost_data
from src.financial_planner.data_ingestion.validation import PlanningValidationError


def create_csv_buffer(data: list[list[str]]) -> StringIO:
    """Helper to generate an in-memory CSV file."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    output.seek(0)
    return output


def test_load_valid_distribution_cost_data():
    """Verify loading of a fully valid annual distribution cost dataset."""
    raw_data = [
        ["Ship to", "Ship to ID", "Distribution Cost"],
        ["Rotterdam Plant", "SHIP-001", "12.50"],
        ["Hamburg Site", "SHIP-014", "18.20"],
    ]

    buffer = create_csv_buffer(raw_data)
    df = load_distribution_cost_data(buffer)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

    # Check Decimal conversion logic
    assert isinstance(df.at[0, "Distribution Cost"], Decimal)
    assert df.at[0, "Distribution Cost"] == Decimal("12.50")
    assert df.at[1, "Distribution Cost"] == Decimal("18.20")


def test_missing_schema_distribution_cost():
    """Verify schema detection on incomplete CSVs."""
    raw_data = [
        ["Ship to", "Ship to ID"],
        ["Rotterdam Plant", "SHIP-001"],
    ]

    buffer = create_csv_buffer(raw_data)

    with pytest.raises(PlanningValidationError) as exc_info:
        load_distribution_cost_data(buffer)

    report = exc_info.value.report
    assert not report.is_valid
    assert any("Missing required column: 'Distribution Cost'" in issue.message for issue in report.issues)


def test_negative_distribution_cost_value():
    """Verify negative distribution costs raise errors."""
    raw_data = [
        ["Ship to", "Ship to ID", "Distribution Cost"],
        ["Rotterdam Plant", "SHIP-001", "-5.50"],
    ]

    buffer = create_csv_buffer(raw_data)

    with pytest.raises(PlanningValidationError) as exc_info:
        load_distribution_cost_data(buffer)

    report = exc_info.value.report
    assert not report.is_valid
    assert any("Distribution Cost cannot be negative" in issue.message for issue in report.issues)


def test_duplicate_ship_to_distribution_cost():
    """Verify duplicate annual distribution costs for the same Ship to are blocked."""
    raw_data = [
        ["Ship to", "Ship to ID", "Distribution Cost"],
        ["Rotterdam Plant", "SHIP-001", "12.50"],
        ["Rotterdam Plant", "SHIP-001", "13.00"],
    ]

    buffer = create_csv_buffer(raw_data)

    with pytest.raises(PlanningValidationError) as exc_info:
        load_distribution_cost_data(buffer)

    report = exc_info.value.report
    assert not report.is_valid
    assert any("Duplicate distribution cost found for Ship to" in issue.message for issue in report.issues)
