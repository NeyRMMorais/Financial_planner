---
name: financial-planning-rules
description: Use for Corporate Finance/FP&A planning applications, especially volume-to-margin modeling, pricing/cost/margin calculations, planning data ingestion, scenario simulation, Streamlit planning workflows, pytest validation, and SAP Analytics Cloud-ready exports. Apply when financial accuracy, Decimal-safe math, zero-volume handling, auditability, and structured reporting datasets matter.
---

# Financial Planning Rules

## Core Mandate

Build FP&A planning workflows as auditable business systems. Favor correctness, clear data contracts, reproducible tests, and enterprise reporting readiness over clever shortcuts.

## Required Workflow

1. Identify the planning step: ingestion, validation, calculation, scenario simulation, UI workflow, or export.
2. Confirm the grain of the data before coding: material, month, sold-to, ship-to, scenario, currency, and unit where relevant.
3. Keep ingestion, calculation, UI, export, and tests in separate modules.
4. Use exact Decimal math for currency, price, cost, margin, and volume-sensitive financial calculations.
5. Handle zero volume, missing values, invalid dates, duplicate grain, and divide-by-zero cases explicitly.
6. Add or update focused pytest coverage for every business rule and edge case added.
7. For UI work, expose validation status and business summaries before calculations run.
8. For export work, produce flat, structured, typed datasets suitable for SAP Analytics Cloud.

## Non-Negotiables

- Do not use binary floats for financial calculations.
- Do not silently coerce missing demand to zero.
- Do not divide by volume unless zero-volume behavior is explicitly defined.
- Do not mix UI code with calculation logic.
- Do not hardcode business assumptions inside formulas when they belong in input tables or assumptions modules.
- Do not export presentation-shaped data when a reporting-tool fact table is needed.

## Reference Loading

Read `references/planning-rules.md` when implementing or reviewing:

- data contracts or schemas
- price, cost, revenue, gross margin, contribution margin, or margin percent formulas
- scenario simulation logic
- SAC export datasets
- validation or reconciliation tests

## Implementation Standards

Use docstrings for functions that encode business logic. State the formula, grain, unit, and zero-volume behavior. Prefer small pure calculation functions that accept validated inputs and return deterministic outputs.

Use pandas or Polars for tabular operations, but keep Decimal values exact. If performance requires scaled integers or Arrow decimal types later, document the representation and prove equivalence with tests before changing calculation behavior.

## Testing Standards

Every planning module should have tests for:

- happy-path reconciliation
- missing required fields
- zero-volume rows
- duplicate grain where uniqueness is required
- exact Decimal totals
- expected output schema
- boundary dates or invalid period values

Use small hand-built fixtures for formula tests and larger generated files for flow tests.
