# Financial Planner - AI Agent Guidelines & Context

This file defines the project-specific rules, domain context, and engineering guidelines for AI agents working on the Financial Planner workspace. 

All agents MUST read and conform to these guidelines.

---

## 🎯 Domain Context & Project Vision

The **Financial Planner** is a Corporate Finance / Financial Planning & Analysis (FP&A) tool. It handles volume-to-margin planning, what-if simulation, and generates structured datasets for upstream planning engines (such as SAP Analytics Cloud).

*   **Primary Input:** Monthly sales volumes in metric tons by Material, Sold-to Customer, and Ship-to Receiving Entity.
*   **Planning Horizon:** The 2026 calendar year (12 periods: `2026-01` through `2026-12`).
*   **Core Logic:** Ingest volume inputs -> Validate schema & constraints -> Apply calculations (price, cost, margin) -> Run simulations -> Export reports.

---

## ⚠️ Hard Constraints & Code Rules

### 1. Decimal Precision (Financial Math)
*   **Rule:** **NEVER** use binary floating-point representation (`float`) for volume calculations, currency figures, pricing, unit costs, or margin metrics.
*   **Implementation:** Always import and use the standard Python `decimal.Decimal` module. 
*   **Example:** Convert CSV string volume fields using `Decimal(value)` in the data loader, and initialize total sums with `Decimal("0.000")`.

### 2. Explicit Edge-Case & Error Handling
*   **Rule:** Do not allow silent data coercion or unhandled exceptions.
*   **Implementation:** 
    *   Zero-volume demand rows are valid planning signals (e.g. indicating no planned shipments for that month but showing commercial presence). Downstream calculations must process zero volumes explicitly without throwing divide-by-zero errors.
    *   Validation errors (e.g., negative volume, duplicates, formatting errors) must be collected and surfaced as structured, human-readable checklists rather than allowing standard library crashes.

### 3. Modularity (Anti-Monolith)
*   **Rule:** Keep logic decoupled.
*   **Structure:**
    *   `data_ingestion/`: File loading and data quality check engine.
    *   `calculations/`: Price, cost, margin, and scenario calculations (pure Python, pandas/polars, fully unit-testable).
    *   `export/`: File generation drivers for SAP Analytics Cloud.
    *   `ui/`: Streamlit dashboard and UI rendering (UI files should be thin wrappers around calculations and ingestion scripts).

---

## 🧪 Testing Guidelines

*   We use `pytest` for all unit testing.
*   The tests must reside in the `tests/` directory and match the structure of the `src/` directory.
*   Tests are run in the shell using:
    ```bash
    python -m pytest
    ```
*   When implementing new features, write corresponding unit tests to verify both happy paths and edge cases (invalid fields, negative numbers, division by zero).
*   **UI Smoke Testing:** To test the Streamlit interface programmatically, agents can use the available `chrome-devtools-plugin` to evaluate page state and run interactive UI checks, avoiding platform-specific shell wrapper scripts where possible.

---

## 📊 Current Development Phase

*   **Calculation Engine (Phase 2):** Core Revenue, Pricing, and Monthly Raw Material Cost calculations have been implemented and validated. Streamlit tabs for Price Planning, Cost Ingestion, and Revenue & Cost Planning are fully active.
*   **Roadmap:** Next we will implement UI simulation controls (Phase 3) and SAC export drivers (Phase 4).

---

## 🔄 Streamlit Development & Reload Protocol

Streamlit runs as a long-running process that hot-reloads the main script (e.g., `app.py`) on changes. However, Python's standard module caching (`sys.modules`) prevents nested imports from being reloaded, leading to stale code execution and `ImportError`s during active development.

To address this, we follow this protocol:

### 1. Automated Module-Cache Clearing
*   **Rule:** The main UI entrypoint (`app.py`) must dynamically delete all cached modules starting with `src.financial_planner` from `sys.modules` at the very beginning of execution.
*   **Code:**
    ```python
    import sys
    for _mod in list(sys.modules.keys()):
        if _mod.startswith("src.financial_planner"):
            del sys.modules[_mod]
    ```
    This forces a clean re-import of all helper modules (e.g., calculations, loaders, validation) whenever the browser is refreshed or a user triggers a rerun.

### 2. Orphaned Port & Process Troubleshooting (Windows)
If port `8501` is blocked or the app displays persistent stale state that browser refresh doesn't clear, run the following troubleshooting protocol in a terminal:

1.  **Check for running Python processes**:
    ```powershell
    wmic process get description,processid | findstr /i "python"
    ```
2.  **Verify port 8501 status and locate owner PID**:
    ```powershell
    netstat -ano | findstr 8501
    ```
3.  **Kill the offending Python process**:
    ```powershell
    taskkill /F /PID <PID>
    ```
4.  **Launch a clean server**:
    ```powershell
    python -m streamlit run src/financial_planner/ui/app.py
    ```
