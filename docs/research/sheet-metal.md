# Sheet Metal / Panel Basics

Research notes for Phase 4 sheet-metal and panel thinking. Last updated: 2026-11-21.

## Fusion 360 / Autodesk Fusion
- Dedicated **Sheet Metal** workspace / tab.
- **Sheet Metal Rules** are foundational: material thickness, bend radius, K-factor (or bend tables), corner reliefs (rectangular / tear / round).
- Primary creation tools:
  - **Base Flange** – from closed sketch profile (starting face).
  - **Edge Flange** – extends an edge by distance + angle with automatic bend.
  - **Contour Flange** – follows open profile (multiple bends in one feature).
  - Hem, Lofted Flange, Bend, Rip, Unfold / Flat Pattern.
- Flat pattern generation is first-class (DXF export for laser/waterjet/CNC).
- Rules can be edited; changes propagate parametrically.
- Bend allowance uses K-factor: BA = (π/180) × angle × (R + K × T).

## Onshape
- **Sheet Metal Model** feature starts a sheet-metal context (Convert / Extrude / Thicken).
- Simultaneous folded + flat pattern + sheet-metal table views (real-time).
- Parameters: thickness, bend radius, K-factor, corner reliefs, min gap.
- Tools: Flange, Hem, Tab, Bend, Jog, Loft, Form (library of punches/embosses).
- Flat pattern lives inside the Part Studio (no external file).
- Supports multi-part sheet-metal models and top-down design.

## Mozaik (manufacturing / panel focus)
- Strong panel / sheet orientation (cabinets, wood panels, also metal).
- Nesting is central: Optimizer places parts on sheets (true-shape or rectangular), with trim, grain, flip-sheet machining, onion-skin / tabs for small parts.
- Cut lists + nesting drive G-code.
- Material / stock library drives sheet size, thickness, grain, CNC eligibility.
- Flip-sheet and 6th-face machining for parts that need work on both sides.

## Key physical parameters (all three tools)
- **Thickness (T)** – constant gauge.
- **Inside bend radius (R)** – set by tooling.
- **K-factor** – neutral-axis location as fraction of thickness (typically 0.33–0.50). Lower for tight R/T.
- Bend allowance / deduction for accurate flat-pattern length.
- Corner reliefs to prevent tearing.

## Nesting concepts (early)
- Rectangular or true-shape packing of flat patterns / panels onto stock sheets.
- Inputs: part outlines (or bounding boxes), sheet size, kerf/trim, grain direction, quantities.
- Outputs: sheet layouts, yield %, remnant handling.
- Mozaik-style: per-cabinet sequencing, flip-sheet support.

## PyModeler design decisions (this increment)
- New schema-validated **SheetMetalRule** (and SheetMetalRuleStore) capturing thickness, inside bend radius, K-factor, optional relief type and unit.
- Helper `bend_allowance(thickness, radius, k_factor, angle_deg)` implementing the standard formula.
- Starter rules (mild steel, aluminum) via `create_default_sheet_metal_rules()`.
- No full flange feature or flat-pattern generator yet (later increments).
- Nesting remains a future stub (schema + simple rectangular packer planned next).
- Aligns with existing MaterialStore (sheet materials can reference a rule later).

## References
- Autodesk Fusion Sheet Metal help (flanges, rules, flat pattern)
- Onshape Sheet Metal Model / tools documentation
- Mozaik nesting / Optimizer guides
- Standard bend-allowance formula: BA = (π/180) × A × (R + K × T)
