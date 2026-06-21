"""Tests for the planning volume ingestion contract."""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pandas as pd
import pytest

from scripts.generate_raw_volume_test_file import (
    ROW_COUNT,
    TARGET_VOLUME_TONS,
    generate_rows,
)
from src.financial_planner.data_ingestion.data_loader import (
    PLANNING_VOLUME_COLUMNS,
    load_planning_volume_data,
    validate_volume_dataset,
)


def test_load_planning_volume_data_matches_expected_schema() -> None:
    """The raw input file should load with the exact agreed source columns."""

    volume_data = load_planning_volume_data()

    assert list(volume_data.columns) == PLANNING_VOLUME_COLUMNS


def test_load_planning_volume_data_has_expected_row_count() -> None:
    """The development raw file should contain the agreed test population."""

    volume_data = load_planning_volume_data()

    assert len(volume_data) == ROW_COUNT


def test_load_planning_volume_data_total_volume_is_exact_decimal() -> None:
    """Total tons should reconcile exactly without binary float rounding."""

    volume_data = load_planning_volume_data()

    assert sum(volume_data["Volume"], Decimal("0.000")) == TARGET_VOLUME_TONS


def test_load_planning_volume_data_uses_only_2026_months() -> None:
    """The current development file should cover only the 2026 planning year."""

    volume_data = load_planning_volume_data()

    assert volume_data["Date"].min() == pd.Period("2026-01", freq="M")
    assert volume_data["Date"].max() == pd.Period("2026-12", freq="M")
    assert len(volume_data["Date"].unique()) == 12


def test_load_planning_volume_data_keeps_volume_as_decimal() -> None:
    """Volume values must stay Decimal so downstream math stays precise."""

    volume_data = load_planning_volume_data()

    assert volume_data["Volume"].map(lambda value: isinstance(value, Decimal)).all()


def test_load_planning_volume_data_accepts_uploaded_file_like_source() -> None:
    """The Streamlit upload path should use the same ingestion validation."""

    csv_source = StringIO(
        "\n".join(
            [
                ",".join(PLANNING_VOLUME_COLUMNS),
                (
                    "Premium Resin A,MAT-1001,2026-01,CUST-001,"
                    "Northstar Manufacturing BV,SHIP-001-NL,"
                    "Northstar Manufacturing BV - Rotterdam Plant,PLANT-01,25.667"
                ),
            ]
        )
    )

    volume_data = load_planning_volume_data(csv_source)

    assert len(volume_data) == 1
    assert volume_data.loc[0, "Date"] == pd.Period("2026-01", freq="M")
    assert volume_data.loc[0, "Volume"] == Decimal("25.667")


def test_generated_raw_rows_reconcile_to_target_volume() -> None:
    """The raw file generator should produce the same tested volume total."""

    rows = generate_rows()
    total_volume = sum((Decimal(row["Volume"]) for row in rows), Decimal("0.000"))

    assert len(rows) == ROW_COUNT
    assert total_volume == TARGET_VOLUME_TONS


def test_validate_volume_dataset_rejects_missing_required_column() -> None:
    """Schema drift should fail before calculations start."""

    volume_data = load_planning_volume_data().drop(columns=["Ship to ID"])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_volume_dataset(volume_data)


def test_validate_volume_dataset_rejects_missing_required_value() -> None:
    """Blank demand inputs should not be silently treated as zero volume."""

    volume_data = load_planning_volume_data()
    volume_data.loc[0, "Volume"] = pd.NA

    with pytest.raises(ValueError, match="Required columns contain missing values"):
        validate_volume_dataset(volume_data)


def test_validate_volume_dataset_rejects_non_decimal_volume() -> None:
    """Accidental float volume values should be rejected explicitly."""

    volume_data = load_planning_volume_data()
    volume_data.loc[0, "Volume"] = 25.667

    with pytest.raises(TypeError, match="Volume must use Decimal values"):
        validate_volume_dataset(volume_data)
