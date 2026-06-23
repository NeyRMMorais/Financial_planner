"""Streamlit interface for the volume planning ingestion workflow."""

from __future__ import annotations

import sys

# Force reload of local project modules on Streamlit rerun to avoid stale imports/errors
for _mod in list(sys.modules.keys()):
    if _mod.startswith("src.financial_planner"):
        del sys.modules[_mod]

from decimal import Decimal
from io import BytesIO

import pandas as pd
import streamlit as st

from src.financial_planner.data_ingestion.data_loader import (
    DEFAULT_RAW_VOLUME_FILE,
    PLANNING_VOLUME_COLUMNS,
    load_planning_volume_data,
)
from src.financial_planner.data_ingestion.price_loader import (
    DEFAULT_RAW_PRICE_FILE,
    load_pricing_data,
)
from src.financial_planner.data_ingestion.cost_loader import (
    DEFAULT_RAW_COST_FILE,
    load_cost_data,
)
from src.financial_planner.data_ingestion.variable_cost_loader import (
    DEFAULT_RAW_VAR_COST_FILE,
    load_variable_cost_data,
)
from src.financial_planner.data_ingestion.distribution_cost_loader import (
    load_distribution_cost_data,
)
from src.financial_planner.data_ingestion.validation import (
    PlanningValidationError,
    ValidationReport,
    validate_grain_uniqueness,
    validate_pricing_completeness,
    validate_cost_completeness,
    run_cost_validation,
    validate_variable_cost_completeness,
    run_variable_cost_validation,
    validate_dist_cost_completeness,
    run_dist_cost_validation,
)
from src.financial_planner.calculations.pricing import (
    PriceOverride,
    resolve_monthly_prices,
)
from src.financial_planner.calculations.pipeline import run_simulation_pipeline, generate_summary_metrics


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


def format_currency(value: Decimal) -> str:
    """Format a Decimal value as a business-readable currency string."""

    return f"${value:,.2f}"


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


def render_checklist(report: ValidationReport) -> None:
    """Render a visual checklist of data quality checks with status emojis."""

    issues = report.issues

    schema_status = "passed" if not any("Missing required column" in i.message for i in issues) else "failed"
    nulls_status = "passed" if not any("Value is missing or blank" in i.message for i in issues) else "failed"
    dates_status = "passed" if not any(i.column == "Date" for i in issues) else "failed"
    volumes_status = "passed" if not any(i.column == "Volume" for i in issues) else "failed"

    grain_issues = [i for i in issues if "Duplicate grain combination" in i.message]
    grain_status = "passed" if not grain_issues else "warning"

    st.markdown("### 🔍 Data Quality Ingestion Checklist")

    def status_emoji(status: str) -> str:
        if status == "passed":
            return "🟢 **PASSED**"
        if status == "warning":
            return "🟡 **WARNING**"
        return "🔴 **FAILED**"

    st.markdown(
        f"""
        - {status_emoji(schema_status)} **Schema Verification**: Checks if all required columns are present.
        - {status_emoji(nulls_status)} **Required Values Check**: Checks for missing, null, or blank planning entries.
        - {status_emoji(dates_status)} **Period & Date Validation**: Ensures date cells are in `YYYY-MM` format and within the 2026 horizon.
        - {status_emoji(volumes_status)} **Volume Format & Sign Check**: Ensures volumes are valid positive numeric quantities.
        - {status_emoji(grain_status)} **Unique Grain Verification**: Checks for duplicate planning combination lines (Material, Customer, Ship-to, Date).
        """
    )


def render_troubleshooting_table(report: ValidationReport) -> None:
    """Render a troubleshooting data table detailing errors and warnings."""

    issues = report.issues
    if not issues:
        return

    st.markdown("### 🛠️ Ingestion Troubleshooting Panel")

    issue_records = []
    for issue in issues:
        severity_badge = "🚨 Error" if issue.severity == "error" else "⚠️ Warning"
        issue_records.append(
            {
                "Severity": severity_badge,
                "Row": "Dataset-wide" if issue.row_index is None else f"Row {issue.row_index}",
                "Column": issue.column,
                "Invalid Value": str(issue.value) if issue.value is not None else "N/A",
                "Message": issue.message,
            }
        )

    st.dataframe(
        pd.DataFrame(issue_records),
        use_container_width=True,
        hide_index=True,
    )


def render_price_checklist(report: ValidationReport) -> None:
    """Render a visual checklist of pricing data quality checks with status emojis."""

    issues = report.issues

    schema_status = "passed" if not any("Missing required column" in i.message for i in issues) else "failed"
    nulls_status = "passed" if not any("Value is missing or blank" in i.message for i in issues) else "failed"
    values_status = "passed" if not any(i.column == "Price" for i in issues) else "failed"
    grain_status = "passed" if not any("Duplicate pricing grain combination" in i.message for i in issues) else "failed"

    st.markdown("### 🔍 Price Ingestion Checklist")

    def status_emoji(status: str) -> str:
        if status == "passed":
            return "🟢 **PASSED**"
        return "🔴 **FAILED**"

    st.markdown(
        f"""
        - {status_emoji(schema_status)} **Schema Verification**: Checks if all required columns are present.
        - {status_emoji(nulls_status)} **Required Values Check**: Checks for missing or blank pricing entries.
        - {status_emoji(values_status)} **Price Format & Sign Check**: Ensures prices are valid non-negative quantities.
        - {status_emoji(grain_status)} **Unique Grain Verification**: Ensures exactly one price record exists per combination.
        """
    )


def render_pricing_data(base_prices: pd.DataFrame) -> None:
    """Render the pricing overview, overrides manager, and final prices preview."""

    st.success("Base pricing data validated successfully!")

    # Render checklist showing everything passed
    report = ValidationReport(is_valid=True, issues=[])
    render_price_checklist(report)

    # Tabs within the pricing tab to organize overrides and previews
    sub_tab1, sub_tab2 = st.tabs(["➕ Add Override Adjustments", "📋 Active Adjustments & Price Preview"])

    with sub_tab1:
        st.subheader("Price Override Adjustments")

        # Dropdowns populated from loaded base prices
        unique_customers = sorted(base_prices["Sold to ID"].unique())
        selected_cust = st.selectbox("Select Customer (Sold to ID)", options=unique_customers, key="ov_cust")

        filtered_ships = base_prices[base_prices["Sold to ID"] == selected_cust]
        unique_ships = sorted(filtered_ships["Ship to ID"].unique())
        selected_ship = st.selectbox("Select Ship-to Destination", options=unique_ships, key="ov_ship")

        filtered_mats = filtered_ships[filtered_ships["Ship to ID"] == selected_ship]
        unique_mats = sorted(filtered_mats["Material ID"].unique())

        if not unique_mats:
            st.warning("No products found for this customer and ship-to combination.")
            return

        selected_mat = st.selectbox("Select Product (Material ID)", options=unique_mats, key="ov_mat")

        # Fetch base price
        base_record = filtered_mats[filtered_mats["Material ID"] == selected_mat]
        current_base = base_record["Price"].values[0] if not base_record.empty else Decimal("0.00")

        st.info(f"Original Base Price: {current_base:,.2f} USD")

        # Start Month
        months = [f"2026-{m:02d}" for m in range(1, 13)]
        selected_month_str = st.selectbox("Override Start Month (Propagates Forward)", options=months, key="ov_month")
        selected_month = pd.Period(selected_month_str, freq="M")

        # New Price Input
        new_price_val = st.number_input(
            "New Unit Price (USD / ton)",
            min_value=0.0,
            value=float(current_base),
            step=10.0,
            key="ov_price_input",
        )

        if st.button("Apply Price Override", key="ov_apply_btn"):
            override = PriceOverride(
                material_id=selected_mat,
                sold_to_id=selected_cust,
                ship_to_id=selected_ship,
                start_month=selected_month,
                new_price=Decimal(f"{new_price_val:.2f}"),
            )

            # Check if override already exists, update if so
            existing_idx = None
            for idx, ov in enumerate(st.session_state.price_overrides):
                if (
                    ov.material_id == selected_mat
                    and ov.sold_to_id == selected_cust
                    and ov.ship_to_id == selected_ship
                    and ov.start_month == selected_month
                ):
                    existing_idx = idx
                    break

            if existing_idx is not None:
                st.session_state.price_overrides[existing_idx] = override
                st.success(
                    f"Updated override for {selected_mat} starting {selected_month_str} to {new_price_val:.2f} USD"
                )
            else:
                st.session_state.price_overrides.append(override)
                st.success(
                    f"Added override for {selected_mat} starting {selected_month_str} to {new_price_val:.2f} USD"
                )

            st.rerun()

    with sub_tab2:
        # Manage active overrides
        overrides = st.session_state.price_overrides

        col_list, col_actions = st.columns([2, 1])

        with col_list:
            st.subheader("Active Price Overrides")
            if not overrides:
                st.info("No active price overrides. All combinations will resolve to their base prices.")
            else:
                records = []
                for idx, ov in enumerate(overrides):
                    records.append(
                        {
                            "Index": idx + 1,
                            "Product": ov.material_id,
                            "Customer": ov.sold_to_id,
                            "Ship-to": ov.ship_to_id,
                            "Start Month": str(ov.start_month),
                            "New Price": f"{ov.new_price:,.2f}",
                        }
                    )
                st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)

        with col_actions:
            st.subheader("Override Actions")
            if overrides:
                override_to_remove = st.selectbox(
                    "Select override to remove by Index",
                    options=[r["Index"] for r in records],
                    key="remove_selectbox",
                )
                if st.button("Remove Selected Override", key="remove_btn"):
                    st.session_state.price_overrides.pop(override_to_remove - 1)
                    st.success("Override removed.")
                    st.rerun()
                if st.button("Clear All Overrides", key="clear_all_btn"):
                    st.session_state.price_overrides = []
                    st.success("All overrides cleared.")
                    st.rerun()
            else:
                st.write("No actions available.")

        st.markdown("---")

        # Display resolved prices preview
        st.subheader("Final Resolved Monthly Prices Preview (First 100 Rows)")
        resolved_df = resolve_monthly_prices(base_prices, overrides)

        display_df = resolved_df.copy()
        display_df["Date"] = display_df["Date"].astype(str)
        display_df["Price"] = display_df["Price"].map(lambda val: f"{val:,.2f}")

        st.dataframe(
            display_df.head(100),
            use_container_width=True,
            hide_index=True,
        )


def render_volume_data(volume_data: pd.DataFrame) -> None:
    """Render the core planning file validation summary and preview."""

    # Check for grain warnings
    grain_issues = validate_grain_uniqueness(volume_data)
    report = ValidationReport(is_valid=True, issues=grain_issues)

    st.success("Volume input validated successfully!")
    render_checklist(report)

    if report.issues:
        render_troubleshooting_table(report)

    st.subheader("Ingestion Profile Metrics")
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


def render_cost_checklist(report: ValidationReport) -> None:
    """Render a visual checklist of cost data quality checks with status emojis."""

    issues = report.issues

    schema_status = "passed" if not any("Missing required column" in i.message for i in issues) else "failed"
    nulls_status = "passed" if not any("Value is missing or blank" in i.message for i in issues) else "failed"
    values_status = "passed" if not any(i.column == "Cost" for i in issues) else "failed"
    periods_status = "passed" if not any("Period must be" in i.message or "Planning period year" in i.message for i in issues) else "failed"
    grain_status = "passed" if not any("Duplicate cost grain combination" in i.message for i in issues) else "failed"

    st.markdown("### 🔍 Cost Ingestion Checklist")

    def status_emoji(status: str) -> str:
        if status == "passed":
            return "🟢 **PASSED**"
        return "🔴 **FAILED**"

    st.markdown(
        f"""
        - {status_emoji(schema_status)} **Schema Verification**: Checks if all required columns are present.
        - {status_emoji(nulls_status)} **Required Values Check**: Checks for missing or blank cost entries.
        - {status_emoji(values_status)} **Cost Format & Sign Check**: Ensures RM costs are valid non-negative quantities.
        - {status_emoji(periods_status)} **Period Verification**: Ensures periods are in 2026 YYYY-MM format.
        - {status_emoji(grain_status)} **Unique Grain Verification**: Ensures exactly one cost record exists per (Plant, Material, Period).
        """
    )


def render_cost_data(base_costs: pd.DataFrame) -> None:
    """Render the cost overview and raw dataset preview."""

    st.success("Monthly raw material cost data validated successfully!")

    report = ValidationReport(is_valid=True, issues=[])
    render_cost_checklist(report)

    st.write("### Base Monthly Raw Material Costs Preview (Top 100 rows)")
    display_costs = base_costs.copy()
    display_costs["Date"] = display_costs["Date"].astype(str)
    display_costs["Cost"] = display_costs["Cost"].map(format_currency)

    st.dataframe(
        display_costs.head(100),
        use_container_width=True,
        hide_index=True,
        column_order=["Plant", "Material ID", "Period", "Cost"],
    )


def render_var_cost_checklist(report: ValidationReport) -> None:
    """Render a visual checklist of variable cost data quality checks with status emojis."""

    issues = report.issues

    schema_status = "passed" if not any("Missing required column" in i.message for i in issues) else "failed"
    nulls_status = "passed" if not any("Value is missing or blank" in i.message for i in issues) else "failed"
    values_status = "passed" if not any(i.column == "Variable Cost" for i in issues) else "failed"
    grain_status = "passed" if not any("Duplicate variable cost" in i.message for i in issues) else "failed"

    st.markdown("### 🔍 Variable Cost Ingestion Checklist")

    def status_emoji(status: str) -> str:
        if status == "passed":
            return "🟢 **PASSED**"
        return "🔴 **FAILED**"

    st.markdown(
        f"""
        - {status_emoji(schema_status)} **Schema Verification**: Checks if all required columns are present.
        - {status_emoji(nulls_status)} **Required Values Check**: Checks for missing or blank cost entries.
        - {status_emoji(values_status)} **Cost Format & Sign Check**: Ensures variable costs are valid non-negative quantities.
        - {status_emoji(grain_status)} **Unique Grain Verification**: Ensures exactly one cost record exists per Material ID.
        """
    )


def render_var_cost_data(base_var_costs: pd.DataFrame) -> None:
    """Render the variable cost overview and raw dataset preview."""

    st.success("Annual variable cost data validated successfully!")

    report = ValidationReport(is_valid=True, issues=[])
    render_var_cost_checklist(report)

    st.write("### Base Annual Variable Costs Preview (Top 100 rows)")
    display_costs = base_var_costs.copy()
    display_costs["Variable Cost"] = display_costs["Variable Cost"].map(format_currency)

    st.dataframe(
        display_costs.head(100),
        use_container_width=True,
        hide_index=True,
        column_order=["Material", "Material ID", "Variable Cost"],
    )


def render_dist_cost_checklist(report: ValidationReport) -> None:
    """Render a visual checklist of distribution cost data quality checks with status emojis."""

    issues = report.issues

    schema_status = "passed" if not any("Missing required column" in i.message for i in issues) else "failed"
    nulls_status = "passed" if not any("Value is missing or blank" in i.message for i in issues) else "failed"
    values_status = "passed" if not any(i.column == "Distribution Cost" for i in issues) else "failed"
    grain_status = "passed" if not any("Duplicate distribution cost" in i.message for i in issues) else "failed"

    st.markdown("### 🔍 Distribution Cost Ingestion Checklist")

    def status_emoji(status: str) -> str:
        if status == "passed":
            return "🟢 **PASSED**"
        return "🔴 **FAILED**"

    st.markdown(
        f"""
        - {status_emoji(schema_status)} **Schema Verification**: Checks if all required columns are present.
        - {status_emoji(nulls_status)} **Required Values Check**: Checks for missing or blank cost entries.
        - {status_emoji(values_status)} **Cost Format & Sign Check**: Ensures distribution costs are valid non-negative quantities.
        - {status_emoji(grain_status)} **Unique Grain Verification**: Ensures exactly one cost record exists per Ship to ID.
        """
    )


def render_dist_cost_data(base_dist_costs: pd.DataFrame) -> None:
    """Render the distribution cost overview and raw dataset preview."""

    st.success("Annual distribution cost data validated successfully!")

    report = ValidationReport(is_valid=True, issues=[])
    render_dist_cost_checklist(report)

    st.write("### Base Annual Distribution Costs Preview (Top 100 rows)")
    display_costs = base_dist_costs.copy()
    display_costs["Distribution Cost"] = display_costs["Distribution Cost"].map(format_currency)

    st.dataframe(
        display_costs.head(100),
        use_container_width=True,
        hide_index=True,
        column_order=["Ship to", "Ship to ID", "Distribution Cost"],
    )


def main() -> None:
    """Run the Streamlit app for the first planning workflow step."""

    # Initialize session state variables for volumes, base prices, overrides, and costs
    if "volume_data" not in st.session_state:
        st.session_state.volume_data = None
    if "base_prices" not in st.session_state:
        st.session_state.base_prices = None
    if "price_overrides" not in st.session_state:
        st.session_state.price_overrides = []
    if "base_costs" not in st.session_state:
        st.session_state.base_costs = None
    if "base_var_costs" not in st.session_state:
        st.session_state.base_var_costs = None
    if "base_dist_costs" not in st.session_state:
        st.session_state.base_dist_costs = None

    st.title("Financial Planner - Ingestion & Adjustments")

    # Cross-Table Ingestion Completeness Check (Price)
    has_price_issues = False
    if st.session_state.volume_data is not None and st.session_state.base_prices is not None:
        price_issues = validate_pricing_completeness(
            st.session_state.volume_data, st.session_state.base_prices
        )
        if price_issues:
            has_price_issues = True
            st.error("🚨 Missing Unit Prices: Active planned sales combinations lack base prices.")
            missing_price_records = [
                {
                    "Active Planned Combination": issue.value,
                    "Reconciliation Error": issue.message,
                }
                for issue in price_issues
            ]
            st.dataframe(pd.DataFrame(missing_price_records), use_container_width=True, hide_index=True)
        else:
            st.success("🟢 Price Ingestion Reconciled: All planned sales combinations have base prices configured.")

    # Cross-Table Ingestion Completeness Check (Cost)
    has_cost_issues = False
    if st.session_state.volume_data is not None and st.session_state.base_costs is not None:
        cost_issues = validate_cost_completeness(
            st.session_state.volume_data, st.session_state.base_costs
        )
        if cost_issues:
            has_cost_issues = True
            st.error("🚨 Missing Raw Material Costs: Active planned volume records lack monthly RM costs.")
            missing_cost_records = [
                {
                    "Active Planned combination & Period": issue.value,
                    "Reconciliation Error": issue.message,
                }
                for issue in cost_issues
            ]
            st.dataframe(pd.DataFrame(missing_cost_records), use_container_width=True, hide_index=True)
        else:
            st.success("🟢 Cost Ingestion Reconciled: All planned sales records have monthly RM costs configured.")

    # Cross-Table Ingestion Completeness Check (Variable Cost)
    has_var_cost_issues = False
    if st.session_state.volume_data is not None and st.session_state.base_var_costs is not None:
        var_cost_issues = validate_variable_cost_completeness(
            st.session_state.volume_data, st.session_state.base_var_costs
        )
        if var_cost_issues:
            has_var_cost_issues = True
            st.error("🚨 Missing Variable Costs: Active planned volume records lack annual variable costs.")
            missing_var_cost_records = [
                {
                    "Active Planned combination": issue.value,
                    "Reconciliation Error": issue.message,
                }
                for issue in var_cost_issues
            ]
            st.dataframe(pd.DataFrame(missing_var_cost_records), use_container_width=True, hide_index=True)
        else:
            st.success("🟢 Variable Cost Ingestion Reconciled: All planned sales records have annual variable costs configured.")

    # Cross-Table Ingestion Completeness Check (Distribution Cost)
    has_dist_cost_issues = False
    if st.session_state.volume_data is not None and st.session_state.base_dist_costs is not None:
        dist_cost_issues = validate_dist_cost_completeness(
            st.session_state.volume_data, st.session_state.base_dist_costs
        )
        if dist_cost_issues:
            has_dist_cost_issues = True
            st.error("🚨 Missing Distribution Costs: Active planned volume records lack distribution costs.")
            missing_dist_cost_records = [
                {
                    "Active Planned combination": issue.value,
                    "Reconciliation Error": issue.message,
                }
                for issue in dist_cost_issues
            ]
            st.dataframe(pd.DataFrame(missing_dist_cost_records), use_container_width=True, hide_index=True)
        else:
            st.success("🟢 Distribution Cost Ingestion Reconciled: All planned sales records have distribution costs configured.")

    tab_volume, tab_price, tab_cost, tab_var_cost, tab_dist_cost, tab_revenue = st.tabs([
        "📊 Volume Ingestion",
        "💵 Price Planning",
        "🏭 RM Cost Ingestion",
        "🏭 Variable Cost Ingestion",
        "🚚 Distribution Cost Ingestion",
        "💰 Revenue & Cost Planning"
    ])

    with tab_volume:
        st.subheader("Monthly Sales Volume Ingestion")
        method = st.radio(
            "Choose how to load your planning volume file:",
            options=["Load from Server Path", "Upload CSV File"],
            key="vol_method",
            horizontal=True,
        )

        volume_data = None
        validation_error_report = None

        if method == "Load from Server Path":
            st.markdown(
                "Use this option to load data directly from the server's filesystem, "
                "avoiding WebSocket transfer issues in sandboxed or forwarded environments."
            )
            from pathlib import Path
            file_path_str = st.text_input("Server File Path", value=str(DEFAULT_RAW_VOLUME_FILE), key="vol_path")
            if st.button("Load Volume Data", key="vol_load_btn"):
                try:
                    file_path = Path(file_path_str)
                    if not file_path.exists():
                        st.error(f"File not found: {file_path}")
                    else:
                        volume_data = load_planning_volume_data(file_path)
                        st.session_state.volume_data = volume_data
                except PlanningValidationError as error:
                    validation_error_report = error.report
                except Exception as error:
                    st.error(str(error))
        else:
            uploaded_file = st.file_uploader(
                "Upload volume input",
                type=["csv"],
                accept_multiple_files=False,
                key="vol_uploader",
            )

            if uploaded_file is not None:
                try:
                    volume_data = load_planning_volume_data(uploaded_file)
                    st.session_state.volume_data = volume_data
                except PlanningValidationError as error:
                    validation_error_report = error.report
                except Exception as error:
                    st.error(str(error))

        if st.session_state.volume_data is not None:
            render_volume_data(st.session_state.volume_data)
        elif validation_error_report is not None:
            st.error("Volume input validation failed with critical errors.")
            render_checklist(validation_error_report)
            render_troubleshooting_table(validation_error_report)
        else:
            st.info("Waiting for volume input data...")

    with tab_price:
        st.subheader("Base Customer/Product Pricing Ingestion")
        p_method = st.radio(
            "Choose how to load your planning base prices file:",
            options=["Load from Server Path", "Upload CSV File"],
            key="price_method",
            horizontal=True,
        )

        p_validation_error = None

        if p_method == "Load from Server Path":
            st.markdown(
                "Use this option to load base pricing directly from the server's filesystem, "
                "avoiding WebSocket transfer issues in sandboxed or forwarded environments."
            )
            from pathlib import Path
            p_file_path_str = st.text_input("Server Price File Path", value=str(DEFAULT_RAW_PRICE_FILE), key="price_path")
            if st.button("Load Price Data", key="price_load_btn"):
                try:
                    p_file_path = Path(p_file_path_str)
                    if not p_file_path.exists():
                        st.error(f"File not found: {p_file_path}")
                    else:
                        st.session_state.base_prices = load_pricing_data(p_file_path)
                except PlanningValidationError as error:
                    p_validation_error = error.report
                except Exception as error:
                    st.error(str(error))
        else:
            p_uploaded_file = st.file_uploader(
                "Upload base prices input",
                type=["csv"],
                accept_multiple_files=False,
                key="price_uploader",
            )

            if p_uploaded_file is not None:
                try:
                    st.session_state.base_prices = load_pricing_data(p_uploaded_file)
                except PlanningValidationError as error:
                    p_validation_error = error.report
                except Exception as error:
                    st.error(str(error))

        if st.session_state.base_prices is not None:
            render_pricing_data(st.session_state.base_prices)
        elif p_validation_error is not None:
            st.error("Pricing validation failed with critical errors.")
            render_price_checklist(p_validation_error)
            render_troubleshooting_table(p_validation_error)
        else:
            st.info("Waiting for base pricing data...")

    with tab_cost:
        st.subheader("Monthly Raw Material Cost Ingestion")
        c_method = st.radio(
            "Choose how to load your planning monthly costs file:",
            options=["Load from Server Path", "Upload CSV File"],
            key="cost_method",
            horizontal=True,
        )

        c_validation_error = None

        if c_method == "Load from Server Path":
            st.markdown(
                "Use this option to load monthly RM costs directly from the server's filesystem, "
                "avoiding WebSocket transfer issues in sandboxed or forwarded environments."
            )
            from pathlib import Path
            c_file_path_str = st.text_input("Server Cost File Path", value=str(DEFAULT_RAW_COST_FILE), key="cost_path")
            if st.button("Load Cost Data", key="cost_load_btn"):
                try:
                    c_file_path = Path(c_file_path_str)
                    if not c_file_path.exists():
                        st.error(f"File not found: {c_file_path}")
                    else:
                        st.session_state.base_costs = load_cost_data(c_file_path)
                except PlanningValidationError as error:
                    c_validation_error = error.report
                except Exception as error:
                    st.error(str(error))
        else:
            c_uploaded_file = st.file_uploader(
                "Upload monthly costs input",
                type=["csv"],
                accept_multiple_files=False,
                key="cost_uploader",
            )

            if c_uploaded_file is not None:
                try:
                    st.session_state.base_costs = load_cost_data(c_uploaded_file)
                except PlanningValidationError as error:
                    c_validation_error = error.report
                except Exception as error:
                    st.error(str(error))

        if st.session_state.base_costs is not None:
            render_cost_data(st.session_state.base_costs)
        elif c_validation_error is not None:
            st.error("Cost validation failed with critical errors.")
            render_cost_checklist(c_validation_error)
            render_troubleshooting_table(c_validation_error)
        else:
            st.info("Waiting for monthly raw material cost data...")

    with tab_var_cost:
        st.subheader("Annual Variable Production Cost Ingestion")
        vc_method = st.radio(
            "Choose how to load your planning annual variable costs file:",
            options=["Load from Server Path", "Upload CSV File"],
            key="var_cost_method",
            horizontal=True,
        )

        vc_validation_error = None

        if vc_method == "Load from Server Path":
            st.markdown(
                "Use this option to load annual variable costs directly from the server's filesystem, "
                "avoiding WebSocket transfer issues in sandboxed or forwarded environments."
            )
            from pathlib import Path
            vc_file_path_str = st.text_input("Server Variable Cost File Path", value=str(DEFAULT_RAW_VAR_COST_FILE), key="var_cost_path")
            if st.button("Load Variable Cost Data", key="var_cost_load_btn"):
                try:
                    vc_file_path = Path(vc_file_path_str)
                    if not vc_file_path.exists():
                        st.error(f"File not found: {vc_file_path}")
                    else:
                        st.session_state.base_var_costs = load_variable_cost_data(vc_file_path)
                except PlanningValidationError as error:
                    vc_validation_error = error.report
                except Exception as error:
                    st.error(str(error))
        else:
            vc_uploaded_file = st.file_uploader(
                "Upload annual variable costs input",
                type=["csv"],
                accept_multiple_files=False,
                key="var_cost_uploader",
            )

            if vc_uploaded_file is not None:
                try:
                    st.session_state.base_var_costs = load_variable_cost_data(vc_uploaded_file)
                except PlanningValidationError as error:
                    vc_validation_error = error.report
                except Exception as error:
                    st.error(str(error))

        if st.session_state.base_var_costs is not None:
            render_var_cost_data(st.session_state.base_var_costs)
        elif vc_validation_error is not None:
            st.error("Variable Cost validation failed with critical errors.")
            render_var_cost_checklist(vc_validation_error)
            render_troubleshooting_table(vc_validation_error)
        else:
            st.info("Waiting for annual variable cost data...")

    with tab_dist_cost:
        st.subheader("Annual Distribution Cost Ingestion")
        dc_method = st.radio(
            "Choose how to load your planning distribution costs file:",
            options=["Load from Server Path", "Upload CSV File"],
            key="dist_cost_method",
            horizontal=True,
        )

        dc_validation_error = None

        if dc_method == "Load from Server Path":
            st.markdown(
                "Use this option to load distribution costs directly from the server's filesystem, "
                "avoiding WebSocket transfer issues in sandboxed or forwarded environments."
            )
            from pathlib import Path
            DEFAULT_RAW_DIST_COST_FILE = Path(__file__).resolve().parents[3] / "data" / "raw" / "mock_distribution_cost_input.csv"
            dc_file_path_str = st.text_input("Server Distribution Cost File Path", value=str(DEFAULT_RAW_DIST_COST_FILE), key="dist_cost_path")
            if st.button("Load Distribution Cost Data", key="dist_cost_load_btn"):
                try:
                    dc_file_path = Path(dc_file_path_str)
                    if not dc_file_path.exists():
                        st.error(f"File not found: {dc_file_path}")
                    else:
                        st.session_state.base_dist_costs = load_distribution_cost_data(dc_file_path)
                except PlanningValidationError as error:
                    dc_validation_error = error.report
                except Exception as error:
                    st.error(str(error))
        else:
            dc_uploaded_file = st.file_uploader(
                "Upload distribution costs input",
                type=["csv"],
                accept_multiple_files=False,
                key="dist_cost_uploader",
            )

            if dc_uploaded_file is not None:
                try:
                    st.session_state.base_dist_costs = load_distribution_cost_data(dc_uploaded_file)
                except PlanningValidationError as error:
                    dc_validation_error = error.report
                except Exception as error:
                    st.error(str(error))

        if st.session_state.base_dist_costs is not None:
            render_dist_cost_data(st.session_state.base_dist_costs)
        elif dc_validation_error is not None:
            st.error("Distribution Cost validation failed with critical errors.")
            render_dist_cost_checklist(dc_validation_error)
            render_troubleshooting_table(dc_validation_error)
        else:
            st.info("Waiting for distribution cost data...")

    with tab_revenue:
        st.subheader("Planning Revenue & Cost Calculations")
        if (
            st.session_state.volume_data is None
            or st.session_state.base_prices is None
            or st.session_state.base_costs is None
            or st.session_state.base_var_costs is None
            or st.session_state.base_dist_costs is None
        ):
            st.info(
                "Waiting for sales volume, base pricing, RM costs, variable costs, and distribution costs data to be loaded..."
            )
        else:
            price_issues = validate_pricing_completeness(
                st.session_state.volume_data, st.session_state.base_prices
            )
            cost_issues = validate_cost_completeness(
                st.session_state.volume_data, st.session_state.base_costs
            )
            var_cost_issues = validate_variable_cost_completeness(
                st.session_state.volume_data, st.session_state.base_var_costs
            )
            dist_cost_issues = validate_dist_cost_completeness(
                st.session_state.volume_data, st.session_state.base_dist_costs
            )

            if price_issues or cost_issues or var_cost_issues or dist_cost_issues:
                if price_issues:
                    st.warning(
                        "🚨 Cannot calculate planning revenue: There are missing unit prices. "
                        "Please resolve the pricing gaps in the 'Price Planning' tab before proceeding."
                    )
                if cost_issues:
                    st.warning(
                        "🚨 Cannot calculate planning costs: There are missing monthly RM costs. "
                        "Please resolve the cost gaps in the 'RM Cost Ingestion' tab before proceeding."
                    )
                if var_cost_issues:
                    st.warning(
                        "🚨 Cannot calculate planning costs: There are missing variable costs. "
                        "Please resolve the cost gaps in the 'Variable Cost Ingestion' tab before proceeding."
                    )
                if dist_cost_issues:
                    st.warning(
                        "🚨 Cannot calculate planning costs: There are missing distribution costs. "
                        "Please resolve the cost gaps in the 'Distribution Cost Ingestion' tab before proceeding."
                    )
            else:
                # 1. Resolve final monthly prices (with overrides applied)
                resolved_prices = resolve_monthly_prices(
                    st.session_state.base_prices, st.session_state.price_overrides
                )

                try:
                    # 2. Run simulation pipeline
                    calculated_df = run_simulation_pipeline(
                        volume_df=st.session_state.volume_data,
                        resolved_prices=resolved_prices,
                        base_costs=st.session_state.base_costs,
                        base_var_costs=st.session_state.base_var_costs,
                        base_dist_costs=st.session_state.base_dist_costs,
                    )

                    # 3. Generate summary metrics
                    metrics = generate_summary_metrics(calculated_df)

                    # 4. Render summary metrics cards
                    st.markdown("#### Total Volume, Revenue & Margin")
                    cols1 = st.columns(4)
                    cols1[0].metric("Total Volume (T)", format_decimal(metrics["total_volume"]))
                    cols1[1].metric("Total Revenue ($)", format_currency(metrics["total_revenue"]))
                    cols1[2].metric("Total VCM ($)", format_currency(metrics["total_vcm"]))
                    cols1[3].metric("Avg VCM ($/T)", format_currency(metrics["weighted_avg_vcm"]))

                    st.markdown("#### Operational Costs")
                    cols2 = st.columns(4)
                    cols2[0].metric("Total RM Cost ($)", format_currency(metrics["total_rm_cost"]))
                    cols2[1].metric("Total Var Cost ($)", format_currency(metrics["total_var_cost"]))
                    cols2[2].metric("Total Dist Cost ($)", format_currency(metrics["total_dist_cost"]))
                    cols2[3].metric("Avg Price ($/T)", format_currency(metrics["weighted_avg_price"]))

                    st.markdown("---")

                    # 5. Display preview of the calculated dataset
                    st.write("### Calculated Planning Dataset Preview (Top 100 rows)")

                    display_df = calculated_df.copy()
                    display_df["Date"] = display_df["Date"].astype(str)
                    display_df["Volume"] = display_df["Volume"].map(format_decimal)
                    display_df["Price"] = display_df["Price"].map(format_currency)
                    display_df["Revenue"] = display_df["Revenue"].map(format_currency)
                    display_df["Cost"] = display_df["Cost"].map(format_currency)
                    display_df["Total RM Cost"] = display_df["Total RM Cost"].map(format_currency)
                    display_df["Variable Cost"] = display_df["Variable Cost"].map(format_currency)
                    display_df["Total Variable Cost"] = display_df["Total Variable Cost"].map(format_currency)
                    display_df["Distribution Cost"] = display_df["Distribution Cost"].map(format_currency)
                    display_df["Total Distribution Cost"] = display_df["Total Distribution Cost"].map(format_currency)
                    display_df["VCM"] = display_df["VCM"].map(format_currency)
                    display_df["Unit VCM"] = display_df["Unit VCM"].map(format_currency)

                    st.dataframe(
                        display_df.head(100),
                        use_container_width=True,
                        hide_index=True,
                        column_order=[
                            "Material",
                            "Material ID",
                            "Plant",
                            "Ship to",
                            "Ship to ID",
                            "Date",
                            "Volume",
                            "Price",
                            "Revenue",
                            "Cost",
                            "Total RM Cost",
                            "Variable Cost",
                            "Total Variable Cost",
                            "Distribution Cost",
                            "Total Distribution Cost",
                            "Unit VCM",
                            "VCM",
                        ],
                    )

                    # 6. Export functionality
                    csv = calculated_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Calculated Financial Plan (CSV)",
                        data=csv,
                        file_name="calculated_financial_plan_2026.csv",
                        mime="text/csv",
                        key="dl_revenue_cost_btn",
                    )
                except Exception as e:
                    st.error(f"An error occurred during calculations: {e}")


if __name__ == "__main__":
    main()
