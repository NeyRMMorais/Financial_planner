# Product

## Register

product

## Users
FP&A (Financial Planning & Analysis) and Corporate Finance managers. They operate on standard desktop monitors, often running our application side-by-side with Microsoft Excel or SAP. They require high data density, clear visual structure, and highly readable numbers to perform monthly volume-to-margin planning and scenario simulation.

## Product Purpose
To manage, simulate, and export monthly volume-to-margin plans for the 2026 calendar year. The application ingests sales volumes, applies exchange rates, price lists, and raw material costs, runs simulations, preserves version-controlled scenarios with detailed change logs, and exports structured datasets to upstream planning engines like SAP Analytics Cloud. Success means zero calculation latency, precise scenario comparisons, and highly efficient data entry.

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
