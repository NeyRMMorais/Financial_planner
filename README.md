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
   * Business calculations and validations are written in pure Python packages to remain fully unit-testable outside of any Streamlit UI components.
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
│   └── generate_raw_volume_test_file.py
├── src/
│   └── financial_planner/
│       ├── calculations/    # Volume, price, cost, margin, and scenario calculations
│       │   ├── costs.py
│       │   ├── pricing.py
│       │   └── revenue.py
│       ├── data_ingestion/  # Raw source loading, validation schemas, and ingestion logs
│       │   ├── cost_loader.py
│       │   ├── data_loader.py
│       │   ├── price_loader.py
│       │   └── validation.py
│       ├── export/          # Structured outputs formatted for SAC
│       │   └── __init__.py
│       └── ui/              # Streamlit dashboard and UI view layers
│           └── app.py
├── tests/                   # PyTest test suite organized by module
│   ├── calculations/
│   │   ├── test_cost_calculations.py
│   │   ├── test_pricing_calculations.py
│   │   └── test_revenue.py
│   └── data_ingestion/
│       ├── test_cost_loader.py
│       ├── test_data_loader.py
│       ├── test_price_loader.py
│       └── test_validation.py
├── pytest.ini               # PyTest configurations (disables cache writes)
└── requirements.txt         # Project package dependencies
```

---

## 📊 Project Status & Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 1: Ingestion & Validation** | Validate 2026 sales volumes, base customer product pricing, monthly plant-specific raw material costs, and cross-dataset grain completeness checks. | **Completed** |
| **Phase 2: Calculation Engine** | Implement price propagation overrides, unit costs, and Decimal-safe revenue and raw material cost calculation logic. | **In Progress** (Pricing, Revenue, and RM Cost calculations completed; Other Variable Costs & Gross Margin pending) |
| **Phase 3: Scenario & Simulations** | Add dashboard sliders to adjust price/cost trends and run what-if simulations. | *Planned* |
| **Phase 4: SAC Export Driver** | Export planning results to SAC-compliant CSV/Excel formats. | *Planned* |

---

## 🛠️ Developer Setup & Commands

### 1. Requirements & Dependencies
Ensure you are using Python 3.10+ and install the dependencies from the project root:
```bash
pip install -r requirements.txt
```

### 2. Running the Streamlit UI
To start the planning ingestion dashboard:
```bash
python -m streamlit run src/financial_planner/ui/app.py
```
The app will run locally and can be accessed at: [http://localhost:8501](http://localhost:8501)

### 3. Running Tests
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
