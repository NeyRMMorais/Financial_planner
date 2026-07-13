# Financial Planner

An automated volume-to-margin planning and simulation application designed for Corporate Finance and Financial Planning & Analysis (FP&A).

This application provides a mathematically precise, performant foundation for monthly planning, scenario simulation, and structured export to enterprise reporting systems like SAP Analytics Cloud (SAC).

---

## 🎯 Project Vision & Key Principles

In corporate finance, precision and traceability are critical. The application is built on three core pillars:

1. **Financial and Mathematical Accuracy**:
   * **Exact Decimal Math**: We never use binary floating-point representation (`float`) for planning volumes or financial currency metrics. All calculations utilize the Python `Decimal` module to prevent rounding discrepancies.
   * **Explicit Edge-Case Handling**: Zero-volume demand lines and missing inputs are explicitly checked, validated, and processed downstream to avoid divide-by-zero crashes or silent assumption failures.
2. **Modular & Clean Architecture**:
   * Complete separation of concerns between data ingestion, calculations, user interface views, and export drivers.
   * Business calculations and validations are written in pure Python packages to remain fully unit-testable outside of any UI components.
3. **Structured Integration**:
   * The ingestion process enforces a strict data schema.
   * Structured, clean outputs are generated specifically for seamless upload/integration with SAP Analytics Cloud (SAC) and corporate database schemas.

---

## 📂 Modular Structure

```text
Financial_planner/
├── .agents/                 # Workspace-scoped rules and agent guidelines
│   └── AGENTS.md            # Guidelines for AI coding agents
├── data/
│   ├── processed/           # Cleaned and planning-ready datasets
│   └── raw/                 # Source extracts before transformation
│       ├── mock_cost_input.csv    # Plant-specific monthly raw material unit costs
│       ├── mock_price_input.csv   # Customer-specific product pricing
│       └── mock_volume_input.csv  # 3,000 monthly volume rows for 2026 (77k tons total)
├── scripts/                 # Repeatable development utility scripts
│   ├── create_test_scenarios.py
│   ├── generate_raw_volume_test_file.py
│   ├── pack_codebase.py
│   └── wipe_app_data.py
├── src/
│   └── financial_planner/
│       ├── calculations/    # Volume, price, cost, margin, scenario, and bridge calculations
│       │   ├── bridge.py
│       │   ├── costs.py
│       │   ├── margin.py
│       │   ├── pipeline.py
│       │   ├── pricing.py
│       │   └── revenue.py
│       ├── data_ingestion/  # Raw source loading, validation schemas, and scenario management
│       │   ├── cost_loader.py
│       │   ├── data_loader.py
│       │   ├── distribution_cost_loader.py
│       │   ├── fx_loader.py
│       │   ├── price_loader.py
│       │   ├── scenario_manager.py
│       │   ├── validation.py
│       │   └── variable_cost_loader.py
│       ├── export/          # Structured outputs formatted for SAC
│       │   └── __init__.py
│       ├── ui/              # React/Vite + shadcn/ui frontend
│       │   └── frontend/
│       │       ├── src/
│       │       │   ├── components/  # Layout, charts, scenario dashboard widgets
│       │       │   ├── routes/      # TanStack Router file-based pages
│       │       │   ├── store/       # Zustand application state management
│       │       │   ├── styles.css   # Main stylesheet
│       │       │   ├── main.tsx     # Client entry point
│       │       │   └── router.tsx   # Router configuration
│       │       └── package.json
│       └── api/             # FastAPI backend (REST API + static file server)
│           ├── main.py
│           ├── routes.py
│           └── schemas.py
├── tests/                   # PyTest test suite organized by module
│   ├── api/
│   │   └── test_routes.py
│   ├── calculations/
│   │   ├── test_bridge.py
│   │   ├── test_cost_calculations.py
│   │   ├── test_margin.py
│   │   ├── test_pipeline.py
│   │   ├── test_pricing_calculations.py
│   │   └── test_revenue.py
│   └── data_ingestion/
│       ├── test_cost_loader.py
│       ├── test_data_loader.py
│       ├── test_distribution_cost_loader.py
│       ├── test_fx_loader.py
│       ├── test_price_loader.py
│       ├── test_scenario_manager.py
│       ├── test_validation.py
│       └── test_variable_cost_loader.py
├── pytest.ini               # PyTest configurations
└── requirements.txt         # Project package dependencies
```

---

## 📊 Project Status & Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 1: Ingestion & Validation** | Validate 2026 sales volumes, base customer product pricing, monthly plant-specific raw material costs, and cross-dataset grain completeness checks. | **Completed** |
| **Phase 2: Calculation Engine** | Price propagation overrides, unit costs, Decimal-safe revenue and raw material cost calculation logic. Full FastAPI API layer and React/Vite frontend. | **Completed** |
| **Phase 3: Scenario & Simulations** | Add UI simulation controls to adjust price/cost trends and run what-if simulations. | *Planned* |
| **Phase 4: SAC Export Driver** | Export planning results to SAC-compliant CSV/Excel formats. | *Planned* |

---

## 🛠️ Developer Setup & Commands

### 1. Requirements & Dependencies
Ensure you are using Python 3.10+ and install the dependencies from the project root:
```bash
pip install -r requirements.txt
```

### 2. Running the App (Development Mode)

Start both servers in separate terminals:

**Terminal 1 — FastAPI backend:**
```bash
uvicorn src.financial_planner.api.main:app --reload --port 8000
```

**Terminal 2 — React/Vite frontend:**
```bash
cd src/financial_planner/ui/frontend
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)** in your browser.

> The Vite dev server proxies all `/api` requests to the FastAPI backend on port 8000.

### 3. Running in Production Mode
Build and serve everything from a single FastAPI port:
```bash
cd src/financial_planner/ui/frontend && npm run build && cd ../../../..
uvicorn src.financial_planner.api.main:app --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)**.
We use `pytest` for unit test coverage. Run the tests using the module format to respect Python paths:
```bash
python -m pytest
```

### 4. Regenerating Mock Data
To regenerate the 3,000-row 2026 development mock input file:
```bash
python scripts/generate_raw_volume_test_file.py
```

---

## 📋 Data Schema Contracts

### Volume Planning Ingestion Input
The raw file must contain the following columns exactly (non-nullable except for `Volume` which can be `0.000` but not empty):

*   **`Material`**: Product name description (string).
*   **`Material ID`**: Unique product identifier code, e.g. `MAT-1001` (string).
*   **`Date`**: The monthly period of the planning row in `YYYY-MM` format, constrained to the 2026 planning year.
*   **`Sold to ID`**: Customer identifier code, e.g. `CUST-001` (string).
*   **`Sold to`**: Corporate customer name description (string).
*   **`Ship to ID`**: Receiving entity/warehouse location code, e.g. `SHIP-001-NL` (string).
*   **`Ship to`**: Receiving entity location description (string).
*   **`Plant`**: Manufacturing/shipping plant identifier, e.g. `PLANT-01` (string).
*   **`Volume`**: Quantity measured in metric tons (numeric string in raw CSV, parsed to `Decimal` in memory).

### Price Planning Ingestion Input
The raw price configuration file must contain:

*   **`Sold to ID`**: Customer identifier code, e.g. `CUST-001` (string).
*   **`Ship to ID`**: Receiving entity location code, e.g. `SHIP-001-NL` (string).
*   **`Material ID`**: Unique product identifier code, e.g. `MAT-1001` (string).
*   **`Price`**: Unit selling price per metric ton (numeric string in raw CSV, parsed to `Decimal` in memory).

### Raw Material Cost Planning Ingestion Input
The raw monthly plant-specific raw material cost configuration file must contain:

*   **`Plant`**: Manufacturing/shipping plant identifier, e.g. `PLANT-01` (string).
*   **`Material ID`**: Unique product identifier code, e.g. `MAT-1001` (string).
*   **`Period`**: The monthly period of the raw material cost in `YYYY-MM` format, constrained to the 2026 planning year.
*   **`Cost`**: Raw material unit cost per metric ton (numeric string in raw CSV, parsed to `Decimal` in memory).

### Variable Cost Planning Ingestion Input
The raw variable cost configuration file must contain:

*   **`Material`**: Product name description (string).
*   **`Material ID`**: Unique product identifier code, e.g. `MAT-1001` (string).
*   **`Variable Cost`**: Variable unit cost per metric ton (numeric string in raw CSV, parsed to `Decimal` in memory).

### Distribution Cost Planning Ingestion Input
The raw distribution cost configuration file must contain:

*   **`Ship to`**: Receiving entity location description (string).
*   **`Ship to ID`**: Receiving entity location code, e.g. `SHIP-001-NL` (string).
*   **`Distribution Cost`**: Distribution unit cost per metric ton (numeric string in raw CSV, parsed to `Decimal` in memory).

### FX Rates Ingestion Input
The raw foreign exchange rates configuration file must contain:

*   **`Period`**: The monthly period of the FX rate in `YYYY-MM` format, constrained to the 2026 planning year.
*   **`Currency`**: Currency code, e.g. `EUR`, `BRL`, `USD` (string).
*   **`Rate`**: Conversion rate against base planning currency (numeric string in raw CSV, parsed to `Decimal` in memory).

### Plant Currency Ingestion Input
The raw plant currency mapping file must contain:

*   **`Plant`**: Manufacturing/shipping plant identifier, e.g. `PLANT-01` (string).
*   **`Currency`**: Operating currency code of the plant, e.g. `EUR`, `BRL` (string).
