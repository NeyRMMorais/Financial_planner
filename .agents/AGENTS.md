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
    *   `ui/frontend/`: React/Vite + FluentUI 2 frontend application.
    *   `api/`: FastAPI backend that exposes all calculations and scenario management as a REST API. The `ui/` layer must remain a thin pass-through — no business logic.

---

## 🧪 Testing Guidelines

*   We use `pytest` for all unit testing.
*   The tests must reside in the `tests/` directory and match the structure of the `src/` directory.
*   Tests are run in the shell using:
    ```bash
    python -m pytest
    ```
*   When implementing new features, write corresponding unit tests to verify both happy paths and edge cases (invalid fields, negative numbers, division by zero).
*   **UI Smoke Testing:** To test the React frontend programmatically, agents can use the available `chrome-devtools-plugin` to evaluate page state and run interactive UI checks against the running Vite dev server (`http://localhost:5173`).

---

## 📊 Current Development Phase

*   **UI Migration (complete):** Streamlit has been fully removed. The React/Vite + FluentUI 2 frontend (`ui/frontend/`) is now the sole UI layer, backed by the FastAPI backend (`api/`).
*   **Calculation Engine (Phase 2, complete):** Core Revenue, Pricing, and Monthly Raw Material Cost calculations have been implemented and validated. All features are exposed via FastAPI routes and consumed by the React frontend.
*   **Roadmap:** Next we will implement UI simulation controls (Phase 3) and SAC export drivers (Phase 4).

---

## 🔄 Development Server Protocol

The application runs as two co-operating processes during local development:

| Process | Command | Default Port | Purpose |
|---|---|---|---|
| FastAPI backend | `uvicorn src.financial_planner.api.main:app --reload --port 8000` | 8000 | REST API + scenario engine |
| Vite dev server | `cd src/financial_planner/ui/frontend && npm run dev` | 5173 | React frontend with HMR |

The Vite dev server proxies all `/api` requests to FastAPI (configured in `vite.config.ts`). Open **`http://localhost:5173`** in your browser.

### Orphaned Port & Process Troubleshooting (Windows)
If port `8000` or `5173` is blocked, run the following:

1.  **Locate owner PID for a port** (replace `8000` with the blocked port):
    ```powershell
    netstat -ano | findstr 8000
    ```
2.  **Kill the offending process**:
    ```powershell
    taskkill /F /PID <PID>
    ```
3.  **Re-launch the backend**:
    ```powershell
    uvicorn src.financial_planner.api.main:app --reload --port 8000
    ```

### Production Mode
Build the React frontend and serve everything from FastAPI on a single port:
```powershell
cd src/financial_planner/ui/frontend
npm run build
cd ../../../..
python -m uvicorn src.financial_planner.api.main:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** — FastAPI will serve the compiled static assets from `ui/frontend/dist/`.
