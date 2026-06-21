import csv
from decimal import Decimal
from io import StringIO
import pytest
import pandas as pd

from src.financial_planner.data_ingestion.variable_cost_loader import load_variable_cost_data
from src.financial_planner.data_ingestion.validation import PlanningValidationError


def create_csv_buffer(data: list[list[str]]) -> StringIO:
    """Helper to generate an in-memory CSV file."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    output.seek(0)
    return output


def test_load_valid_variable_cost_data():
    """Verify loading of a fully valid annual variable cost dataset."""
    raw_data = [
        ["Material", "Material ID", "Variable Cost"],
        ["Polymer A", "MAT-01", "2.50"],
        ["Resin B", "MAT-02", "15.750"],
    ]

    buffer = create_csv_buffer(raw_data)
    df = load_variable_cost_data(buffer)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

    # Check Decimal conversion logic
    assert isinstance(df.at[0, "Variable Cost"], Decimal)
    assert df.at[0, "Variable Cost"] == Decimal("2.50")
    assert df.at[1, "Variable Cost"] == Decimal("15.750")


def test_missing_schema_variable_cost():
    """Verify schema detection on incomplete CSVs."""
    # Missing 'Variable Cost' column
    raw_data = [
        ["Material", "Material ID"],
        ["Polymer A", "MAT-01"],
    ]

    buffer = create_csv_buffer(raw_data)

    with pytest.raises(PlanningValidationError) as exc_info:
        load_variable_cost_data(buffer)

    report = exc_info.value.report
    assert not report.is_valid
    assert any("Missing required column: 'Variable Cost'" in issue.message for issue in report.issues)


def test_negative_variable_cost_value():
    """Verify negative variable costs raise errors."""
    raw_data = [
        ["Material", "Material ID", "Variable Cost"],
        ["Polymer A", "MAT-01", "-2.50"],
    ]

    buffer = create_csv_buffer(raw_data)

    with pytest.raises(PlanningValidationError) as exc_info:
        load_variable_cost_data(buffer)

    report = exc_info.value.report
    assert not report.is_valid
    assert any("Variable Cost cannot be negative" in issue.message for issue in report.issues)


def test_duplicate_material_variable_cost():
    """Verify duplicate annual variable costs for the same material are blocked."""
    raw_data = [
        ["Material", "Material ID", "Variable Cost"],
        ["Polymer A", "MAT-01", "2.50"],
        ["Polymer A", "MAT-01", "3.00"],
    ]

    buffer = create_csv_buffer(raw_data)

    with pytest.raises(PlanningValidationError) as exc_info:
        load_variable_cost_data(buffer)

    report = exc_info.value.report
    assert not report.is_valid
    assert any("Duplicate variable cost" in issue.message for issue in report.issues)
