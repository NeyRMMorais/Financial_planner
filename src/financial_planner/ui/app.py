"""Streamlit interface for the volume planning ingestion workflow."""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO

import pandas as pd
import streamlit as st

from src.financial_planner.data_ingestion.data_loader import (
    DEFAULT_RAW_VOLUME_FILE,
    PLANNING_VOLUME_COLUMNS,
    load_planning_volume_data,
)


st.set_page_config(
    page_title="Volume Planning",
    page_icon="",
    layout="wide",
)


def decimal_sum(values: pd.Series) -> Decimal:
    """Return the exact sum of Decimal values from a planning volume column.

    Formula:
        Total volume tons = sum of row-level volume tons for the uploaded
        planning file. The calculation starts from ``Decimal("0.000")`` to
        avoid binary floating-point conversion.
    """

    return sum(values, Decimal("0.000"))


def format_decimal(value: Decimal) -> str:
    """Format a Decimal value as a business-readable tons string."""

    return f"{value:,.3f}"


def prepare_display_data(volume_data: pd.DataFrame) -> pd.DataFrame:
    """Create a UI-safe copy of planning volume data for tabular display.

    Business logic:
        The ingestion DataFrame keeps Date as monthly Period and Volume as
        Decimal for calculations. Streamlit display receives strings for those
        fields so the UI does not coerce exact Decimal values into floats.
    """

    display_data = volume_data.copy()
    display_data["Date"] = display_data["Date"].astype(str)
    display_data["Volume"] = display_data["Volume"].map(format_decimal)
    return display_data


def render_ingestion_summary(volume_data: pd.DataFrame) -> None:
    """Render the core planning file validation summary.

    Business logic:
        These metrics answer whether the uploaded source file is ready to move
        into calculation: population size, total demand volume, monthly horizon,
        and commercial coverage by material and sold-to customer.
    """

    total_volume = decimal_sum(volume_data["Volume"])
    date_min = str(volume_data["Date"].min())
    date_max = str(volume_data["Date"].max())

    metric_columns = st.columns(5)
    metric_columns[0].metric("Rows", f"{len(volume_data):,}")
    metric_columns[1].metric("Total tons", format_decimal(total_volume))
    metric_columns[2].metric("Period", f"{date_min} to {date_max}")
    metric_columns[3].metric("Materials", f"{volume_data['Material ID'].nunique():,}")
    metric_columns[4].metric("Sold-to", f"{volume_data['Sold to ID'].nunique():,}")


def render_monthly_volume(volume_data: pd.DataFrame) -> None:
    """Render an exact monthly volume summary for the uploaded planning file.

    Formula:
        Monthly volume tons = sum of Decimal row-level volume tons grouped by
        the monthly planning period.
    """

    monthly_rows = []
    for month, month_data in volume_data.groupby("Date", sort=True):
        monthly_rows.append(
            {
                "Date": str(month),
                "Volume": format_decimal(decimal_sum(month_data["Volume"])),
            }
        )

    st.dataframe(
        pd.DataFrame(monthly_rows),
        use_container_width=True,
        hide_index=True,
    )


def render_volume_data(volume_data: pd.DataFrame) -> None:
    """Render the core planning file validation summary and preview."""

    st.success("Volume input validated")
    render_ingestion_summary(volume_data)

    st.subheader("Monthly Volume")
    render_monthly_volume(volume_data)

    st.subheader("Source Preview")
    st.dataframe(
        prepare_display_data(volume_data).head(100),
        use_container_width=True,
        hide_index=True,
        column_order=PLANNING_VOLUME_COLUMNS,
    )


def main() -> None:
    """Run the Streamlit app for the first planning workflow step."""

    st.title("Volume Planning")

    st.subheader("Select Ingestion Method")
    method = st.radio(
        "Choose how to load your planning volume file:",
        options=["Load from Server Path", "Upload CSV File"],
        horizontal=True,
    )

    volume_data = None

    if method == "Load from Server Path":
        st.markdown(
            "Use this option to load data directly from the server's filesystem, "
            "avoiding WebSocket transfer issues in sandboxed or forwarded environments."
        )
        from pathlib import Path
        file_path_str = st.text_input("Server File Path", value=str(DEFAULT_RAW_VOLUME_FILE))
        if st.button("Load Data"):
            try:
                file_path = Path(file_path_str)
                if not file_path.exists():
                    st.error(f"File not found: {file_path}")
                else:
                    volume_data = load_planning_volume_data(file_path)
            except Exception as error:
                st.error(str(error))
    else:
        uploaded_file = st.file_uploader(
            "Upload volume input",
            type=["csv"],
            accept_multiple_files=False,
        )

        if uploaded_file is not None:
            try:
                volume_data = load_planning_volume_data(uploaded_file)
            except Exception as error:
                st.error(str(error))

    if volume_data is not None:
        render_volume_data(volume_data)
    else:
        st.info("Waiting for volume input data...")


if __name__ == "__main__":
    main()
