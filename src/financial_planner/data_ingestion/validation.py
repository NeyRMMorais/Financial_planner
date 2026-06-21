"""Advanced planning data validation engine.

This module defines validation rules, issue structures, and exception types
for sales volume planning inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import re
from typing import Any, Literal

PLANNING_VOLUME_COLUMNS: list[str] = [
    "Material",
    "Material ID",
    "Date",
    "Sold to ID",
    "Sold to",
    "Ship to ID",
    "Ship to",
    "Volume",
]

PLANNING_PRICE_COLUMNS: list[str] = [
    "Sold to ID",
    "Ship to ID",
    "Material ID",
    "Price",
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
