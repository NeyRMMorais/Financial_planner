# Product

## Register

product

## Users
1. **C-Level Executives (CFO, Business Unit Leaders):** Operate in the **Executive Cockpit (Flight Simulator)** to test macro shocks (feedstock, FX, commercial pricing pass-through), review real-time waterfall bridges (isolating Pure Volume vs. Mix effects), and consume AI CFO Briefs and 1-click PowerPoint decks for board meetings.
2. **FP&A Managers & Corporate Finance Controllers:** Operate in the **Planner Workspace** alongside Microsoft Excel and SAP. They require high data density, granular tables, auditable change logs, and atomic-level driver adjustments to manage monthly rolling forecasts and budgets.

## Product Purpose
To manage, simulate, and bridge monthly financial plans for a chemical manufacturing business (9 products across 3 product lines) across a 12-month rolling horizon (2026 baseline). The application ingests volumes, pricing, raw material BOMs, and GL account expenses, cascades top-down assumptions to the atomic grain, reconciles volume/mix/price/cost/FX movements, maintains an auditable financial impact change log, and exports structured datasets to SAP Analytics Cloud. Success means sub-second calculation latency, zero floating-point math errors, and effortless C-suite executive decision-making.

## Brand Personality
Modern, polished, and highly structured corporate productivity. Emulates the shadcn/ui design language with clean layout, physical grounding, subtle depth, and clear container hierarchies.
* **3-word personality:** Structured, Polished, Precise
* **Emotional goals:** Professional confidence, visual calm, expert reliability

## Anti-references
* Stark, flat, borderless minimalism.
* Overly rounded geometry (e.g., cards with 24px+ corners).
* Generic "AI-purple" SaaS landing page gradients and floating blobs.
* Cluttered modal-driven UI that interrupts data entry flow.
* Low-contrast, hard-to-read numeric tables.

## Design Principles
1. **Physical Grounding & Depth:** Use layered backgrounds, subtle drop shadows, and top-edge highlights to create distinct container levels rather than flat, floating shapes.
2. **High-Density Scannability:** Prioritize dense, grid-based information layouts. Text, numbers, and inputs should have comfortable but compact margins, optimized for fast keyboard navigation and side-by-side Excel comparisons.
3. **Strict Geometric Cohesion:** Distinguish layout hierarchy through a locked corner-radius scale: 8px for top-level containers and cards, 4px for interactive elements (buttons, inputs, dropdowns), and pill-shape for AI prompts and tags.
4. **Stateless Visual Auditability:** Every action, active scenario, and difference comparison must be visibly labeled. Never allow silent states; help the planner trace how costs and revenues flow through different simulations.

## Accessibility & Inclusion
* **WCAG AA Compliance:** Strict contrast ratios (minimum 4.5:1) for all data grid cells, placeholders, and helper text.
* **Keyboard Navigation:** High-density data tables and form grids must support arrow keys, tab indexing, and distinct focus indicators.
* **Screen Reader Accessibility:** Proper HTML5 semantic elements and ARIA labels for all planning tables and interactive charts.
* **Reduced Motion:** Provide clean static or instant transitions when `prefers-reduced-motion` is active.
