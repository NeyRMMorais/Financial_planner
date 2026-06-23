"""Advanced planning data validation engine.

This module defines validation rules, issue structures, and exception types
for sales volume planning inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import re
from typing import Any, Literal

import pandas as pd

PLANNING_VOLUME_COLUMNS: list[str] = [
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

PLANNING_PRICE_COLUMNS: list[str] = [
    "Sold to ID",
    "Ship to ID",
    "Material ID",
    "Price",
]

PLANNING_COST_COLUMNS: list[str] = [
    "Plant",
    "Material ID",
    "Period",
    "Cost",
]

PLANNING_VARIABLE_COST_COLUMNS: list[str] = [
    "Material",
    "Material ID",
    "Variable Cost",
]

PLANNING_DIST_COST_COLUMNS: list[str] = [
    "Ship to",
    "Ship to ID",
    "Distribution Cost",
]

PLANNING_FX_COLUMNS: list[str] = [
    "Period",
    "Currency",
    "Rate",
]

PLANNING_PLANT_CURRENCY_COLUMNS: list[str] = [
    "Plant",
    "Currency",
]


@dataclass
class ValidationIssue:
    """Represents a specific validation issue in the planning dataset."""

    column: str
    row_index: int | None  # 1-indexed row number (or None if dataset-wide)
    value: Any
    message: str
    severity: Literal["error", "warning"] = "error"


@dataclass
class ValidationReport:
    """Summary of all issues found during dataset validation."""

    is_valid: bool  # True if there are zero issues with severity == "error"
    issues: list[ValidationIssue] = field(default_factory=list)


class PlanningValidationError(ValueError):
    """Custom exception raised when planning data fails critical validation rules."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        errors_count = sum(1 for issue in report.issues if issue.severity == "error")
        super().__init__(f"Validation failed with {errors_count} critical errors.")


def validate_schema(df: Any) -> list[ValidationIssue]:
    """Verify that all required planning columns are present in the dataset."""

    issues = []
    missing_columns = [
        column for column in PLANNING_VOLUME_COLUMNS if column not in df.columns
    ]
    for column in missing_columns:
        issues.append(
            ValidationIssue(
                column=column,
                row_index=None,
                value=None,
                message=f"Missing required column: '{column}'",
                severity="error",
            )
        )
    return issues


def validate_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    """Verify that no required fields are null, blank, or whitespace-only."""

    issues = []
    check_columns = [
        column for column in PLANNING_VOLUME_COLUMNS if column in df.columns
    ]

    for column in check_columns:
        # Check for NaN / None values
        null_mask = df[column].isna()

        # Check for empty or whitespace-only strings
        str_series = df[column].fillna("").astype(str).str.strip()
        empty_mask = str_series.eq("")

        combined_mask = null_mask | empty_mask
        if combined_mask.any():
            for idx in df[combined_mask].index:
                val = df.at[idx, column]
                issues.append(
                    ValidationIssue(
                        column=column,
                        row_index=int(idx) + 1,  # 1-indexed row number
                        value=val,
                        message="Value is missing or blank",
                        severity="error",
                    )
                )

    return issues


def validate_dates_format_and_range(df: Any) -> list[ValidationIssue]:
    """Verify that date values are YYYY-MM formatted and strictly within 2026."""

    issues = []
    if "Date" not in df.columns:
        return issues

    date_regex = re.compile(r"^\d{4}-\d{2}$")

    for idx, val in df["Date"].items():
        if pd_is_null_like(val):
            continue

        val_str = str(val).strip()
        if not date_regex.match(val_str):
            issues.append(
                ValidationIssue(
                    column="Date",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Date must be in YYYY-MM format (e.g. 2026-01)",
                    severity="error",
                )
            )
            continue

        try:
            year, month = map(int, val_str.split("-"))
            if year != 2026:
                issues.append(
                    ValidationIssue(
                        column="Date",
                        row_index=int(idx) + 1,
                        value=val,
                        message=f"Planning period year is {year}, but must be exactly 2026",
                        severity="error",
                    )
                )
            elif month < 1 or month > 12:
                issues.append(
                    ValidationIssue(
                        column="Date",
                        row_index=int(idx) + 1,
                        value=val,
                        message=f"Month is {month:02d}, but must be between 01 and 12",
                        severity="error",
                    )
                )
        except ValueError:
            issues.append(
                ValidationIssue(
                    column="Date",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Invalid date format",
                    severity="error",
                )
            )

    return issues


def validate_volumes_format_and_sign(df: Any) -> list[ValidationIssue]:
    """Verify that volumes parse to non-negative Decimal values."""

    issues = []
    if "Volume" not in df.columns:
        return issues

    for idx, val in df["Volume"].items():
        if pd_is_null_like(val):
            continue

        if isinstance(val, Decimal):
            if val < 0:
                issues.append(
                    ValidationIssue(
                        column="Volume",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Volume cannot be negative",
                        severity="error",
                    )
                )
            continue

        val_str = str(val).strip()
        if val_str == "":
            continue

        try:
            decimal_value = Decimal(val_str)
            if decimal_value < 0:
                issues.append(
                    ValidationIssue(
                        column="Volume",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Volume cannot be negative",
                        severity="error",
                    )
                )
        except Exception:
            issues.append(
                ValidationIssue(
                    column="Volume",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Volume must be a valid numeric value",
                    severity="error",
                )
            )

    return issues


def validate_grain_uniqueness(df: Any) -> list[ValidationIssue]:
    """Verify there are no duplicate entries for the planning grain.

    Duplicates are treated as warnings because raw input lists might contain
    individual transactional lines that will be aggregated during calculation phases.
    """

    issues = []
    required_grain = ["Material ID", "Sold to ID", "Ship to ID", "Date"]

    for column in required_grain:
        if column not in df.columns:
            return issues

    # Normalise grain columns to string representations for comparison
    temp_df = df[required_grain].copy()
    for col in required_grain:
        temp_df[col] = temp_df[col].astype(str).str.strip()

    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)

    if duplicate_mask.any():
        # Group by the duplicated combinations to list exact rows
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for keys, group in grouped:
            if isinstance(keys, tuple):
                mat_id, cust_id, ship_id, date_val = keys
            else:
                mat_id = keys
                cust_id, ship_id, date_val = "", "", ""

            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Material ID, Sold to ID, Ship to ID, Date",
                    row_index=None,
                    value=f"Material: {mat_id}, Sold-to: {cust_id}, Ship-to: {ship_id}, Date: {date_val}",
                    message=f"Duplicate grain combination found across rows {row_indices}",
                    severity="warning",
                )
            )

    return issues


def pd_is_null_like(val: Any) -> bool:
    """Helper to detect pandas NA/NaN/None values."""

    if val is None:
        return True
    try:
        import pandas as pd

        return pd.isna(val)
    except ImportError:
        return False


def run_advanced_validation(df: Any) -> ValidationReport:
    """Run all validation rules on the raw string planning dataset."""

    issues = []

    # 1. Schema check
    schema_issues = validate_schema(df)
    issues.extend(schema_issues)

    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)

    # 2. Blank fields check
    issues.extend(validate_nulls_and_empty(df))

    # 3. Dates check
    issues.extend(validate_dates_format_and_range(df))

    # 4. Volumes check
    issues.extend(validate_volumes_format_and_sign(df))

    # 5. Grain uniqueness check
    issues.extend(validate_grain_uniqueness(df))

    # Valid if there are no errors (warnings are non-blocking)
    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_price_schema(df: Any) -> list[ValidationIssue]:
    """Verify that all required pricing columns are present in the dataset."""

    issues = []
    missing_columns = [
        column for column in PLANNING_PRICE_COLUMNS if column not in df.columns
    ]
    for column in missing_columns:
        issues.append(
            ValidationIssue(
                column=column,
                row_index=None,
                value=None,
                message=f"Missing required column: '{column}'",
                severity="error",
            )
        )
    return issues


def validate_price_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    """Verify that no required pricing fields are null, blank, or whitespace-only."""

    issues = []
    check_columns = [
        column for column in PLANNING_PRICE_COLUMNS if column in df.columns
    ]

    for column in check_columns:
        null_mask = df[column].isna()
        str_series = df[column].fillna("").astype(str).str.strip()
        empty_mask = str_series.eq("")

        combined_mask = null_mask | empty_mask
        if combined_mask.any():
            for idx in df[combined_mask].index:
                val = df.at[idx, column]
                issues.append(
                    ValidationIssue(
                        column=column,
                        row_index=int(idx) + 1,
                        value=val,
                        message="Value is missing or blank",
                        severity="error",
                    )
                )

    return issues


def validate_price_values(df: Any) -> list[ValidationIssue]:
    """Verify that price values parse to non-negative Decimal values."""

    issues = []
    if "Price" not in df.columns:
        return issues

    for idx, val in df["Price"].items():
        if pd_is_null_like(val):
            continue

        if isinstance(val, Decimal):
            if val < 0:
                issues.append(
                    ValidationIssue(
                        column="Price",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Price cannot be negative",
                        severity="error",
                    )
                )
            continue

        val_str = str(val).strip()
        if val_str == "":
            continue

        try:
            decimal_value = Decimal(val_str)
            if decimal_value < 0:
                issues.append(
                    ValidationIssue(
                        column="Price",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Price cannot be negative",
                        severity="error",
                    )
                )
        except Exception:
            issues.append(
                ValidationIssue(
                    column="Price",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Price must be a valid numeric value",
                    severity="error",
                )
            )

    return issues


def validate_price_grain_uniqueness(df: Any) -> list[ValidationIssue]:
    """Verify that there is exactly one price record per unique planning combination.

    Duplicate price rows are treated as errors because they create ambiguity for calculations.
    """

    issues = []
    required_grain = ["Sold to ID", "Ship to ID", "Material ID"]

    for column in required_grain:
        if column not in df.columns:
            return issues

    temp_df = df[required_grain].copy()
    for col in required_grain:
        temp_df[col] = temp_df[col].astype(str).str.strip()

    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)

    if duplicate_mask.any():
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for keys, group in grouped:
            if isinstance(keys, tuple):
                cust_id, ship_id, mat_id = keys
            else:
                cust_id = keys
                ship_id, mat_id = "", ""

            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Sold to ID, Ship to ID, Material ID",
                    row_index=None,
                    value=f"Customer: {cust_id}, Ship-to: {ship_id}, Material: {mat_id}",
                    message=f"Duplicate pricing grain combination found across rows {row_indices}",
                    severity="error",
                )
            )

    return issues


def run_pricing_validation(df: Any) -> ValidationReport:
    """Run all validation rules on the raw string pricing dataset."""

    issues = []

    schema_issues = validate_price_schema(df)
    issues.extend(schema_issues)

    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)

    issues.extend(validate_price_nulls_and_empty(df))
    issues.extend(validate_price_values(df))
    issues.extend(validate_price_grain_uniqueness(df))

    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_pricing_completeness(
    volume_df: Any, price_df: Any
) -> list[ValidationIssue]:
    """Verify that every combination in the sales volume dataset has a matching price.

    Missing price combinations are treated as errors because they prevent
    revenue and margin calculations.
    """

    issues = []
    grain_cols = ["Sold to ID", "Ship to ID", "Material ID"]

    # Ensure required columns are present in both dataframes
    for col in grain_cols:
        if col not in volume_df.columns or col not in price_df.columns:
            return issues

    # Extract unique combinations from the volume dataset
    vol_grain = volume_df[grain_cols].drop_duplicates()

    # Create a set of unique combinations in the pricing dataset for O(1) lookup
    price_keys = set(
        zip(
            price_df["Sold to ID"].astype(str).str.strip(),
            price_df["Ship to ID"].astype(str).str.strip(),
            price_df["Material ID"].astype(str).str.strip(),
        )
    )

    # Check for missing prices
    for _, row in vol_grain.iterrows():
        cust_id = str(row["Sold to ID"]).strip()
        ship_id = str(row["Ship to ID"]).strip()
        mat_id = str(row["Material ID"]).strip()

        if (cust_id, ship_id, mat_id) not in price_keys:
            issues.append(
                ValidationIssue(
                    column="Price",
                    row_index=None,
                    value=f"Customer: {cust_id}, Ship-to: {ship_id}, Material: {mat_id}",
                    message="Missing unit price in base pricing table",
                    severity="error",
                )
            )

    return issues


def validate_cost_schema(df: Any) -> list[ValidationIssue]:
    """Verify that all required cost columns are present in the dataset."""
    issues = []
    missing_columns = [
        column for column in PLANNING_COST_COLUMNS if column not in df.columns
    ]
    for column in missing_columns:
        issues.append(
            ValidationIssue(
                column=column,
                row_index=None,
                value=None,
                message=f"Missing required column: '{column}'",
                severity="error",
            )
        )
    return issues


def validate_cost_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    """Verify that no required cost fields are null, blank, or whitespace-only."""
    issues = []
    check_columns = [
        column for column in PLANNING_COST_COLUMNS if column in df.columns
    ]

    for column in check_columns:
        null_mask = df[column].isna()
        str_series = df[column].fillna("").astype(str).str.strip()
        empty_mask = str_series.eq("")

        combined_mask = null_mask | empty_mask
        if combined_mask.any():
            for idx in df[combined_mask].index:
                val = df.at[idx, column]
                issues.append(
                    ValidationIssue(
                        column=column,
                        row_index=int(idx) + 1,
                        value=val,
                        message="Value is missing or blank",
                        severity="error",
                    )
                )
    return issues


def validate_cost_values(df: Any) -> list[ValidationIssue]:
    """Verify that cost values parse to non-negative Decimal values."""
    issues = []
    if "Cost" not in df.columns:
        return issues

    for idx, val in df["Cost"].items():
        if pd_is_null_like(val):
            continue

        if isinstance(val, Decimal):
            if val < 0:
                issues.append(
                    ValidationIssue(
                        column="Cost",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Cost cannot be negative",
                        severity="error",
                    )
                )
            continue

        val_str = str(val).strip()
        if val_str == "":
            continue

        try:
            decimal_value = Decimal(val_str)
            if decimal_value < 0:
                issues.append(
                    ValidationIssue(
                        column="Cost",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Cost cannot be negative",
                        severity="error",
                    )
                )
        except Exception:
            issues.append(
                ValidationIssue(
                    column="Cost",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Cost must be a valid numeric value",
                    severity="error",
                )
            )
    return issues


def validate_cost_periods(df: Any) -> list[ValidationIssue]:
    """Verify that Period values are YYYY-MM formatted and strictly within 2026."""
    issues = []
    if "Period" not in df.columns:
        return issues

    period_regex = re.compile(r"^\d{4}-\d{2}$")

    for idx, val in df["Period"].items():
        if pd_is_null_like(val):
            continue

        val_str = str(val).strip()
        if not period_regex.match(val_str):
            issues.append(
                ValidationIssue(
                    column="Period",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Period must be in YYYY-MM format (e.g. 2026-01)",
                    severity="error",
                )
            )
            continue

        try:
            year, month = map(int, val_str.split("-"))
            if year != 2026:
                issues.append(
                    ValidationIssue(
                        column="Period",
                        row_index=int(idx) + 1,
                        value=val,
                        message=f"Planning period year is {year}, but must be exactly 2026",
                        severity="error",
                    )
                )
            elif month < 1 or month > 12:
                issues.append(
                    ValidationIssue(
                        column="Period",
                        row_index=int(idx) + 1,
                        value=val,
                        message=f"Month is {month:02d}, but must be between 01 and 12",
                        severity="error",
                    )
                )
        except ValueError:
            issues.append(
                ValidationIssue(
                    column="Period",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Invalid period format",
                    severity="error",
                )
            )
    return issues


def validate_cost_grain_uniqueness(df: Any) -> list[ValidationIssue]:
    """Verify that there is exactly one cost record per unique cost combination.

    Duplicate cost rows are treated as errors because they create ambiguity for calculations.
    """
    issues = []
    required_grain = ["Plant", "Material ID", "Period"]

    for column in required_grain:
        if column not in df.columns:
            return issues

    temp_df = df[required_grain].copy()
    for col in required_grain:
        temp_df[col] = temp_df[col].astype(str).str.strip()

    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)

    if duplicate_mask.any():
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for keys, group in grouped:
            if isinstance(keys, tuple):
                plant, mat_id, period = keys
            else:
                plant = keys
                mat_id, period = "", ""

            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Plant, Material ID, Period",
                    row_index=None,
                    value=f"Plant: {plant}, Material: {mat_id}, Period: {period}",
                    message=f"Duplicate cost grain combination found across rows {row_indices}",
                    severity="error",
                )
            )
    return issues


def run_cost_validation(df: Any) -> ValidationReport:
    """Run all validation rules on the raw string monthly RM cost dataset."""
    issues = []

    schema_issues = validate_cost_schema(df)
    issues.extend(schema_issues)

    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)

    issues.extend(validate_cost_nulls_and_empty(df))
    issues.extend(validate_cost_values(df))
    issues.extend(validate_cost_periods(df))
    issues.extend(validate_cost_grain_uniqueness(df))

    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_cost_completeness(
    volume_df: Any, cost_df: Any
) -> list[ValidationIssue]:
    """Verify that every combination/month in the volume dataset has a matching raw material cost.

    Missing cost combinations are treated as errors because they prevent cost calculations.
    """
    issues = []
    volume_grain_cols = ["Plant", "Material ID", "Date"]
    cost_grain_cols = ["Plant", "Material ID", "Period"]

    # Ensure required columns are present
    for col in volume_grain_cols:
        if col not in volume_df.columns:
            return issues
    for col in cost_grain_cols:
        if col not in cost_df.columns:
            return issues

    # Create a set of unique combinations in the cost dataset for O(1) lookup
    cost_keys = set(
        zip(
            cost_df["Plant"].astype(str).str.strip(),
            cost_df["Material ID"].astype(str).str.strip(),
            cost_df["Period"].astype(str).str.strip(),
        )
    )

    # Check for missing costs
    for _, row in volume_df.iterrows():
        plant = str(row["Plant"]).strip()
        mat_id = str(row["Material ID"]).strip()
        date_val = str(row["Date"]).strip()

        if (plant, mat_id, date_val) not in cost_keys:
            issues.append(
                ValidationIssue(
                    column="Cost",
                    row_index=None,
                    value=f"Plant: {plant}, Material: {mat_id}, Period: {date_val}",
                    message="Missing raw material cost for combination and period",
                    severity="error",
                )
            )

    return issues


def validate_variable_cost_schema(df: Any) -> list[ValidationIssue]:
    """Verify that all required variable cost columns are present."""
    issues = []
    missing_columns = [
        column for column in PLANNING_VARIABLE_COST_COLUMNS if column not in df.columns
    ]
    for column in missing_columns:
        issues.append(
            ValidationIssue(
                column=column,
                row_index=None,
                value=None,
                message=f"Missing required column: '{column}'",
                severity="error",
            )
        )
    return issues


def validate_variable_cost_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    """Verify that no required variable cost fields are null or blank."""
    issues = []
    check_columns = [
        column for column in PLANNING_VARIABLE_COST_COLUMNS if column in df.columns
    ]

    for column in check_columns:
        null_mask = df[column].isna()
        str_series = df[column].fillna("").astype(str).str.strip()
        empty_mask = str_series.eq("")

        combined_mask = null_mask | empty_mask
        if combined_mask.any():
            for idx in df[combined_mask].index:
                val = df.at[idx, column]
                issues.append(
                    ValidationIssue(
                        column=column,
                        row_index=int(idx) + 1,
                        value=val,
                        message="Value is missing or blank",
                        severity="error",
                    )
                )

    return issues


def validate_variable_cost_values(df: Any) -> list[ValidationIssue]:
    """Verify that variable cost values parse to non-negative Decimal values."""
    issues = []
    if "Variable Cost" not in df.columns:
        return issues

    for idx, val in df["Variable Cost"].items():
        if pd_is_null_like(val):
            continue

        if isinstance(val, Decimal):
            if val < 0:
                issues.append(
                    ValidationIssue(
                        column="Variable Cost",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Variable Cost cannot be negative",
                        severity="error",
                    )
                )
            continue

        val_str = str(val).strip()
        if val_str == "":
            continue

        try:
            decimal_value = Decimal(val_str)
            if decimal_value < 0:
                issues.append(
                    ValidationIssue(
                        column="Variable Cost",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Variable Cost cannot be negative",
                        severity="error",
                    )
                )
        except Exception:
            issues.append(
                ValidationIssue(
                    column="Variable Cost",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Variable Cost must be a valid numeric value",
                    severity="error",
                )
            )
    return issues


def validate_variable_cost_grain_uniqueness(df: Any) -> list[ValidationIssue]:
    """Verify that there is exactly one variable cost record per Material ID."""
    issues = []
    required_grain = ["Material ID"]

    for column in required_grain:
        if column not in df.columns:
            return issues

    temp_df = df[required_grain].copy()
    for col in required_grain:
        temp_df[col] = temp_df[col].astype(str).str.strip()

    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)

    if duplicate_mask.any():
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for mat_id, group in grouped:
            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Material ID",
                    row_index=None,
                    value=f"Material: {mat_id}",
                    message=f"Duplicate variable cost found for Material across rows {row_indices}",
                    severity="error",
                )
            )
    return issues


def run_variable_cost_validation(df: Any) -> ValidationReport:
    """Run all validation rules on the raw string annual variable cost dataset."""
    issues = []

    schema_issues = validate_variable_cost_schema(df)
    issues.extend(schema_issues)

    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)

    issues.extend(validate_variable_cost_nulls_and_empty(df))
    issues.extend(validate_variable_cost_values(df))
    issues.extend(validate_variable_cost_grain_uniqueness(df))

    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_variable_cost_completeness(
    volume_df: Any, var_cost_df: Any
) -> list[ValidationIssue]:
    """Verify that every Material ID in the volume dataset has a matching variable cost."""
    issues = []
    if "Material ID" not in volume_df.columns or "Material ID" not in var_cost_df.columns:
        return issues

    var_cost_keys = set(var_cost_df["Material ID"].astype(str).str.strip())

    for _, row in volume_df.iterrows():
        mat_id = str(row["Material ID"]).strip()

        if mat_id not in var_cost_keys:
            issues.append(
                ValidationIssue(
                    column="Variable Cost",
                    row_index=None,
                    value=f"Material ID: {mat_id}",
                    message="Missing variable cost for Material",
                    severity="error",
                )
            )

    return issues


def validate_dist_cost_schema(df: Any) -> list[ValidationIssue]:
    """Verify that all required distribution cost columns are present."""
    issues = []
    missing_columns = [
        column for column in PLANNING_DIST_COST_COLUMNS if column not in df.columns
    ]
    for column in missing_columns:
        issues.append(
            ValidationIssue(
                column=column,
                row_index=None,
                value=None,
                message=f"Missing required column: '{column}'",
                severity="error",
            )
        )
    return issues


def validate_dist_cost_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    """Verify that no required distribution cost fields are null or blank."""
    issues = []
    check_columns = [
        column for column in PLANNING_DIST_COST_COLUMNS if column in df.columns
    ]

    for column in check_columns:
        null_mask = df[column].isna()
        str_series = df[column].fillna("").astype(str).str.strip()
        empty_mask = str_series.eq("")

        combined_mask = null_mask | empty_mask
        if combined_mask.any():
            for idx in df[combined_mask].index:
                val = df.at[idx, column]
                issues.append(
                    ValidationIssue(
                        column=column,
                        row_index=int(idx) + 1,
                        value=val,
                        message="Value is missing or blank",
                        severity="error",
                    )
                )

    return issues


def validate_dist_cost_values(df: Any) -> list[ValidationIssue]:
    """Verify that distribution cost values parse to non-negative Decimal values."""
    issues = []
    if "Distribution Cost" not in df.columns:
        return issues

    for idx, val in df["Distribution Cost"].items():
        if pd_is_null_like(val):
            continue

        if isinstance(val, Decimal):
            if val < 0:
                issues.append(
                    ValidationIssue(
                        column="Distribution Cost",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Distribution Cost cannot be negative",
                        severity="error",
                    )
                )
            continue

        val_str = str(val).strip()
        if val_str == "":
            continue

        try:
            decimal_value = Decimal(val_str)
            if decimal_value < 0:
                issues.append(
                    ValidationIssue(
                        column="Distribution Cost",
                        row_index=int(idx) + 1,
                        value=val,
                        message="Distribution Cost cannot be negative",
                        severity="error",
                    )
                )
        except Exception:
            issues.append(
                ValidationIssue(
                    column="Distribution Cost",
                    row_index=int(idx) + 1,
                    value=val,
                    message="Distribution Cost must be a valid numeric value",
                    severity="error",
                )
            )
    return issues


def validate_dist_cost_grain_uniqueness(df: Any) -> list[ValidationIssue]:
    """Verify that there is exactly one distribution cost record per Ship to ID."""
    issues = []
    required_grain = ["Ship to ID"]

    for column in required_grain:
        if column not in df.columns:
            return issues

    temp_df = df[required_grain].copy()
    for col in required_grain:
        temp_df[col] = temp_df[col].astype(str).str.strip()

    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)

    if duplicate_mask.any():
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for ship_id, group in grouped:
            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Ship to ID",
                    row_index=None,
                    value=f"Ship to: {ship_id}",
                    message=f"Duplicate distribution cost found for Ship to across rows {row_indices}",
                    severity="error",
                )
            )
    return issues


def run_dist_cost_validation(df: Any) -> ValidationReport:
    """Run all validation rules on the raw string annual distribution cost dataset."""
    issues = []

    schema_issues = validate_dist_cost_schema(df)
    issues.extend(schema_issues)

    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)

    issues.extend(validate_dist_cost_nulls_and_empty(df))
    issues.extend(validate_dist_cost_values(df))
    issues.extend(validate_dist_cost_grain_uniqueness(df))

    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_dist_cost_completeness(
    volume_df: Any, dist_cost_df: Any
) -> list[ValidationIssue]:
    """Verify that every Ship to ID in the volume dataset has a matching distribution cost."""
    issues = []
    if "Ship to ID" not in volume_df.columns or "Ship to ID" not in dist_cost_df.columns:
        return issues

    dist_cost_keys = set(dist_cost_df["Ship to ID"].astype(str).str.strip())

    for _, row in volume_df.iterrows():
        ship_id = str(row["Ship to ID"]).strip()

        if ship_id not in dist_cost_keys:
            issues.append(
                ValidationIssue(
                    column="Distribution Cost",
                    row_index=None,
                    value=f"Ship to ID: {ship_id}",
                    message="Missing distribution cost for Ship to",
                    severity="error",
                )
            )

    return issues


def validate_fx_schema(df: Any) -> list[ValidationIssue]:
    issues = []
    missing_columns = [col for col in PLANNING_FX_COLUMNS if col not in df.columns]
    for col in missing_columns:
        issues.append(
            ValidationIssue(
                column=col,
                row_index=None,
                value=None,
                message=f"Missing required column: '{col}'",
                severity="error",
            )
        )
    return issues


def validate_fx_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    issues = []
    for col in PLANNING_FX_COLUMNS:
        if col not in df.columns:
            continue
        for idx, val in df[col].items():
            if pd.isna(val) or str(val).strip() == "":
                issues.append(
                    ValidationIssue(
                        column=col,
                        row_index=int(idx) + 1,
                        value=val,
                        message=f"Value in '{col}' cannot be blank",
                        severity="error",
                    )
                )
    return issues


def validate_fx_values(df: Any) -> list[ValidationIssue]:
    issues = []
    for idx, row in df.iterrows():
        rate_val = row.get("Rate")
        if pd.isna(rate_val) or str(rate_val).strip() == "":
            continue
        try:
            val = Decimal(str(rate_val).strip())
            if val <= Decimal("0"):
                issues.append(
                    ValidationIssue(
                        column="Rate",
                        row_index=int(idx) + 1,
                        value=rate_val,
                        message="FX rate must be greater than zero",
                        severity="error",
                    )
                )
        except Exception:
            issues.append(
                ValidationIssue(
                    column="Rate",
                    row_index=int(idx) + 1,
                    value=rate_val,
                    message="FX rate must be a valid positive number",
                    severity="error",
                )
            )
    return issues


def validate_fx_periods(df: Any) -> list[ValidationIssue]:
    issues = []
    period_pattern = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
    for idx, row in df.iterrows():
        period = row.get("Period")
        if pd.isna(period) or str(period).strip() == "":
            continue
        period_str = str(period).strip()
        if not period_pattern.match(period_str):
            issues.append(
                ValidationIssue(
                    column="Period",
                    row_index=int(idx) + 1,
                    value=period,
                    message="Period must be in YYYY-MM format",
                    severity="error",
                )
            )
    return issues


def validate_fx_uniqueness(df: Any) -> list[ValidationIssue]:
    issues = []
    required_grain = ["Period", "Currency"]
    for col in required_grain:
        if col not in df.columns:
            return issues
    temp_df = df[required_grain].copy()
    for col in required_grain:
        temp_df[col] = temp_df[col].astype(str).str.strip()
    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)
    if duplicate_mask.any():
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for keys, group in grouped:
            period, currency = keys
            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Currency",
                    row_index=None,
                    value=f"Period: {period}, Currency: {currency}",
                    message=f"Duplicate FX rate found for Currency across rows {row_indices}",
                    severity="error",
                )
            )
    return issues


def run_fx_validation(df: Any) -> ValidationReport:
    issues = []
    schema_issues = validate_fx_schema(df)
    issues.extend(schema_issues)
    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)
    issues.extend(validate_fx_nulls_and_empty(df))
    issues.extend(validate_fx_values(df))
    issues.extend(validate_fx_periods(df))
    issues.extend(validate_fx_uniqueness(df))
    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_plant_currency_schema(df: Any) -> list[ValidationIssue]:
    issues = []
    missing_columns = [col for col in PLANNING_PLANT_CURRENCY_COLUMNS if col not in df.columns]
    for col in missing_columns:
        issues.append(
            ValidationIssue(
                column=col,
                row_index=None,
                value=None,
                message=f"Missing required column: '{col}'",
                severity="error",
            )
        )
    return issues


def validate_plant_currency_nulls_and_empty(df: Any) -> list[ValidationIssue]:
    issues = []
    for col in PLANNING_PLANT_CURRENCY_COLUMNS:
        if col not in df.columns:
            continue
        for idx, val in df[col].items():
            if pd.isna(val) or str(val).strip() == "":
                issues.append(
                    ValidationIssue(
                        column=col,
                        row_index=int(idx) + 1,
                        value=val,
                        message=f"Value in '{col}' cannot be blank",
                        severity="error",
                    )
                )
    return issues


def validate_plant_currency_uniqueness(df: Any) -> list[ValidationIssue]:
    issues = []
    required_grain = ["Plant"]
    if "Plant" not in df.columns:
        return issues
    temp_df = df[required_grain].copy()
    temp_df["Plant"] = temp_df["Plant"].astype(str).str.strip()
    duplicate_mask = temp_df.duplicated(subset=required_grain, keep=False)
    if duplicate_mask.any():
        grouped = temp_df[duplicate_mask].groupby(required_grain)
        for plant, group in grouped:
            plant_name = plant[0] if isinstance(plant, tuple) else plant
            row_indices = [int(i) + 1 for i in group.index]
            issues.append(
                ValidationIssue(
                    column="Plant",
                    row_index=None,
                    value=f"Plant: {plant_name}",
                    message=f"Duplicate Plant currency mapping found across rows {row_indices}",
                    severity="error",
                )
            )
    return issues


def run_plant_currency_validation(df: Any) -> ValidationReport:
    issues = []
    schema_issues = validate_plant_currency_schema(df)
    issues.extend(schema_issues)
    if schema_issues:
        return ValidationReport(is_valid=False, issues=issues)
    issues.extend(validate_plant_currency_nulls_and_empty(df))
    issues.extend(validate_plant_currency_uniqueness(df))
    has_errors = any(issue.severity == "error" for issue in issues)
    return ValidationReport(is_valid=not has_errors, issues=issues)


def validate_fx_completeness(
    volume_df: Any, fx_df: Any, plant_currency_df: Any
) -> list[ValidationIssue]:
    issues = []
    # Check column existence first
    if "Plant" not in volume_df.columns or "Date" not in volume_df.columns:
        return issues
    if "Plant" not in plant_currency_df.columns or "Currency" not in plant_currency_df.columns:
        return issues
    if "Period" not in fx_df.columns or "Currency" not in fx_df.columns:
        return issues

    # Map Plant to Currency for fast lookup
    plant_to_curr = {
        str(row["Plant"]).strip(): str(row["Currency"]).strip()
        for _, row in plant_currency_df.iterrows()
    }
    
    # Set of existing FX combinations (Period, Currency)
    fx_keys = set(
        zip(
            fx_df["Period"].astype(str).str.strip(),
            fx_df["Currency"].astype(str).str.strip(),
        )
    )

    # Check for each volume row
    for _, row in volume_df.iterrows():
        plant = str(row["Plant"]).strip()
        date_val = str(row["Date"]).strip()

        # 1. Check if Plant exists in Mapping
        if plant not in plant_to_curr:
            issues.append(
                ValidationIssue(
                    column="Plant",
                    row_index=None,
                    value=plant,
                    message=f"Plant '{plant}' has no currency mapping",
                    severity="error",
                )
            )
            continue

        lc = plant_to_curr[plant]

        # 2. Check if FX rate exists for LC and Period
        if lc != "USD" and (date_val, lc) not in fx_keys:
            issues.append(
                ValidationIssue(
                    column="Rate",
                    row_index=None,
                    value=f"Period: {date_val}, Currency: {lc}",
                    message="Missing FX rate for plant's local currency",
                    severity="error",
                )
            )

        # 3. Check if FX rate exists for EUR and Period (since RM and variable costs are in EUR)
        if (date_val, "EUR") not in fx_keys:
            issues.append(
                ValidationIssue(
                    column="Rate",
                    row_index=None,
                    value=f"Period: {date_val}, Currency: EUR",
                    message="Missing EUR exchange rate required for RM and Variable cost conversions",
                    severity="error",
                )
            )

    return issues
