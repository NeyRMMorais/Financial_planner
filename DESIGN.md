# Design System

## Theme
shadcn/ui inspired, highly structured layout with physical depth, soft geometry, and high data density.

## Colors
All colors are configured for light and dark modes, utilizing a layered container approach.

### Base Canvases
* **Dark Mode:**
  * Root Background: `#1C1C1C`
  * Elevated Card/Panel Background: `#282828`
  * Sub-elevation/Header Background: `#303030`
* **Light Mode:**
  * Root Background: `#F3F3F3`
  * Elevated Card/Panel Background: `#FFFFFF`
  * Sub-elevation/Header Background: `#FAFAFA`

### Interactive States & Accents
* **Primary Brand Accent:**
  * Base: `#0078D4` (Dark / Light Mode contrast compliant)
  * Hover: `#106EBE`
  * Active/Tactile: `#005A9E`
* **AI/Generative Accent (Copilot Gradient Shimmer):**
  * Gradient: `linear-gradient(135deg, #2870EA 0%, #F54EA2 100%)`
* **Low-Contrast Borders & Dividers:**
  * Dark Mode: `rgba(255, 255, 255, 0.08)`
  * Light Mode: `rgba(0, 0, 0, 0.06)`

### Translucent Materials
* **Floating Overlays (context menus, tooltips, dialogs):**
  * Filter: `backdrop-blur-md`
  * Background (Dark): `rgba(40, 40, 40, 0.75)`
  * Background (Light): `rgba(255, 255, 255, 0.8)`

## Typography
* **Primary Font Stack:** `'Segoe UI Variable', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif`
* **Headings:** Semibold weight (600), tight letter-spacing (`tracking-tight`), slightly muted text contrast.
* **Body & Grids:** Regular weight (400), 14px base font size (`text-sm`), optimized for dense data tables.
* **Metadata/Muted Text:** Regular weight (400), 12px font size (`text-xs`), color `#8A8A8A` / `--text-muted`.

## Geometry & Corner Radius
* **8px (`rounded-lg`):** Top-level structure, content cards, sidebars, dialog windows, chart containers.
* **4px (`rounded` / `rounded-md`):** Interactive inputs, buttons, dropdowns, table cells on focus.
* **9999px (`rounded-full`):** Prompt input bars, badges, status pills, user avatars.

## Spacing & Density
* **Layout Grid:** CSS Grid for dashboard layouts. Standard padding of `p-4` (16px) for content containers.
* **Table Cells:** Compact vertical padding of `py-1.5` (6px) or `py-2` (8px) to maximize rows in viewport.
* **Sidebar Panels:** Persistent or collapsible sidebars (320px–360px) for actions/filters.

## Shadows & Elevation
* **Ambient Drop Shadow:**
  * `box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08)`
* **Top Highlight Border:**
  * Use a subtle top highlight (`border-t border-t-white/10` in dark mode) to simulate physical light hitting the container's top edge.

## Form Controls & Scenario Drivers
* **Numeric Input Boxes over Sliders:** For financial modeling and assumption adjustments, avoid imprecise slider bars. Use clean, compact numeric input boxes with distinct prefix/suffix tags (`%`, `$/MT`, `€`, `$`) and clear step increments.
* **Dual-View UX Hierarchy:**
  * **Executive Cockpit (Flight Simulator):** Macro/commercial driver input boxes, real-time reactive waterfall bridge, Change Log timeline, and AI CFO brief.
  * **Planner Workspace:** Dense Excel-like data grids, raw CSV uploads, and atomic-level diffing tables.

