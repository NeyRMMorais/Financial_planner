# Financial Planner - AI Agent Guidelines & Context

This file defines the project-specific rules, domain context, and engineering guidelines for AI agents working on the Financial Planner workspace. 

All agents MUST read and conform to these guidelines.

---

## 🎯 Domain Context & Project Vision

The **Financial Planner** is a Corporate Finance / Financial Planning & Analysis (FP&A) tool built for a chemical manufacturing business.

*   **Portfolio Hierarchy:** 9 chemical products across 3 product lines:
    *   **Line 1 (Performance Specialties):** High margin (~45-55% VCM).
    *   **Line 2 (Functional Formulations):** High margin (~35-45% VCM).
    *   **Line 3 (Base Intermediates):** Lower margin (~15-22% VCM).
*   **Planning Horizon:** 12-Month Rolling Horizon (Calendar Year 2026 baseline: 12 periods `2026-01` through `2026-12`).
*   **Official Roadmap:** Detailed in [`ROADMAP.md`](file:///c:/Users/Ney/Documents/Financial_planner/ROADMAP.md). All agents must consult `ROADMAP.md` before planning or implementing features.
*   **Core Logic:** Single source of truth at atomic grain (`[Period] × [Plant] × [Customer] × [Material]`) -> Top-down macro assumption cascading -> Standard VCM calculations -> Pure Volume vs. Mix Effect Bridge -> Scenario Change Log with Financial Impact Trail -> AI CFO Brief & Board Deck.

---

## 📊 Current Development Phase & Roadmap

We are executing a **3-Phase Strategy** (see [`ROADMAP.md`](file:///c:/Users/Ney/Documents/Financial_planner/ROADMAP.md) for complete specifications):

*   **Phase 1 (Active Focus - Executive Standard VCM Prototype):**
    1.  Assumption Driver Input Boxes with top-down atomic cascading (Volume, Price, Raw Mat, Var Cost, Dist Cost, FX).
    2.  Scenario Change Log tracking before/after VCM metrics, $ delta, and % impact.
    3.  6-Pillar Bridge Engine separating **Pure Volume Effect** from **Mix Effect** (with product line drill-down).
    4.  AI Executive Brief & 1-Click Board Presentation (`.pptx`).
    5.  Dual-View UI: Executive Cockpit + Planner Workspace.
*   **Phase 2 (Full P&L Expansion):** Ingest GL accounts for manufacturing variances (PPV), plant fixed costs, and SG&A down to EBITDA.
*   **Phase 3 (12-Month Rolling Horizon & Actuals):** Rolling 12-month horizon (Actuals + Forecast) and 3-way comparisons (Actuals vs Budget vs Forecast).

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
    *   `ui/frontend/`: React/Vite + shadcn/ui frontend application.
    *   `api/`: FastAPI backend that exposes all calculations and scenario management as a REST API. The `ui/` layer must remain a thin pass-through — no business logic.

### 4. Terminal Crash Prevention
*   **Rule 1:** **NEVER** print large amounts of data directly to the terminal.
*   **Rule 2:** Redirect long output to temporary files.
*   **Rule 3:** Avoid chaining complex commands with pipes.
*   **Rule 4:** Append `; echo 'DONE'` at the end of executions to verify completion cleanly.

### 5. Production Deployment Restriction
*   **Rule:** **NEVER** build, push, or deploy any changes to production GCP or Cloud Run unless the user explicitly and directly requests it. Focus strictly on local development, testing, and verification. Any deploy commands (e.g. gcloud run deploy) are strictly prohibited unless Ney explicitly requests deployment.

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
