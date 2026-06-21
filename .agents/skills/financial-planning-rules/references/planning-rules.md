# Planning Rules Reference

## Current Application Context

The application is an automated volume-to-margin planning and simulation tool for Corporate Finance/FP&A. It starts with monthly volume input and will evolve into pricing, cost, margin, simulation, UI, and SAP Analytics Cloud export workflows.

Current raw volume input grain:

- Material
- Material ID
- Date, monthly period in YYYY-MM format
- Sold to ID
- Sold to
- Ship to ID
- Ship to
- Volume, in tons

Current development test file target:

- 3,000 rows
- 2026 months only
- total volume exactly 77,000.000 tons

## Data Contract Rules

Required fields must be present and populated. Empty strings, nulls, and missing columns are invalid. Missing volume must not be treated as zero.

Dates should be normalized to month-level periods. Keep daily dates only if the business process explicitly requires daily planning.

Validate grain before calculations. If a table is expected to be unique by material, month, sold-to, ship-to, and scenario, duplicates must either fail validation or be aggregated by an explicit rule.

## Numeric Precision Rules

Use `Decimal` for:

- volume when used in financial formulas
- price per ton
- variable cost per ton
- fixed cost allocations
- revenue
- cost
- gross margin
- contribution margin
- margin percentages

Avoid standard floats. If reading from CSV, read numeric fields as text and convert to Decimal. If showing data in Streamlit, format Decimal values as strings for display when needed to avoid UI float coercion.

Set rounding intentionally at business boundaries, not inside intermediate calculations. Prefer storing unrounded Decimal calculations and rounding only for display or export if the target system requires a scale.

## Core Formula Patterns

At row grain:

- Revenue = Volume tons * Price per ton
- Variable cost = Volume tons * Variable cost per ton
- Contribution margin = Revenue - Variable cost
- Gross margin = Revenue - Cost of goods sold
- Margin per ton = Margin / Volume tons, except when Volume is zero
- Margin percent = Margin / Revenue, except when Revenue is zero

Zero-volume behavior must be explicit:

- Revenue and variable cost from volume-driven formulas should usually calculate to zero.
- Per-ton metrics should return null, Decimal zero, or a labeled not-applicable value by an explicit business rule.
- Percent metrics should not divide by zero revenue.

## Scenario Rules

Scenario calculations should preserve the base input and create separate scenario outputs. Do not overwrite raw input values.

A scenario should carry at least:

- scenario name or ID
- source scenario or baseline reference
- assumption set ID where relevant
- calculation timestamp or run ID when exports need traceability

Scenario formulas should be deterministic from inputs and assumptions.

## SAC Export Rules

Exports for SAP Analytics Cloud should be flat, structured tables, not UI summaries. Prefer long-form fact tables with stable dimension columns and typed measure columns.

Recommended planning output fields as the model evolves:

- Scenario ID
- Date
- Material ID
- Material
- Sold to ID
- Sold to
- Ship to ID
- Ship to
- Volume tons
- Price per ton
- Revenue
- Variable cost per ton
- Variable cost
- Contribution margin
- Gross margin
- Margin percent, if defined
- Currency, if money fields exist
- Unit, for volume fields
- Run ID or version, when needed for auditability

Export tests should assert column order, required columns, row count, data types or serializable formats, and reconciliation totals.

## UI & Streamlit Best Practices

The first UI step should let users upload raw planning input and see validation status before calculations run.

### UI Modularization
- Keep Streamlit views (`src/financial_planner/ui/app.py`) focused strictly on presentation, inputs, widgets, and layout.
- Decouple all heavy computations, file parsing, and business logic into pure Python files under `src/financial_planner/data_ingestion/` and `src/financial_planner/calculations/`.

### Streamlit Performance Guidelines
- **Caching (`@st.cache_data`):** Cache heavy data parsing/loading functions (like loading the CSV file or pre-processing reference tables). Do not cache objects that hold local dynamic state or streamlit-specific widgets.
- **Fragments (`@st.fragment`):** For UI panels that need to update independently (e.g. form inputs or individual charts), wrap them in fragments to prevent full-page script re-runs.
- **Reconciliation & Previews:** For each planning stage, show:
  - what input was accepted
  - what validations passed or failed (visual checklist)
  - core reconciliation totals
  - a preview of source or output rows
  - clear error messages for missing fields, invalid dates, invalid numerics, and zero-division-sensitive calculations
