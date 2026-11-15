# Mozaik Cut Lists, Nesting, Joinery, and Manufacturing Outputs

Research notes for PyModeler. Sources: Mozaik Software product pages, support guides (Cutlist Tab), and industry descriptions. Last updated: 2026-11-15.

## Overview
Mozaik is specialized CAD/CAM software for cabinet, furniture, and casework manufacturers. It emphasizes design-to-manufacture workflows:
- Room layout and cabinet design
- Automatic generation of manufacturing documents from the design
- Support for both manual (table/panel saw) and CNC shops
- Construction methods and joinery rules that adapt the model

Product tiers: Manufacturing (non-CNC), CNC (nesting + G-code), Enterprise (job management, multi-user).

## Cut Lists / Part Lists
- Central Cutlist Tab generates detailed lists of all parts.
- Multiple cutlist types: All Parts, Door Sizes, Door Cutlist, Drawer/Tray lists, Face Frames, Panel Stock, Counter Tops, etc.
- Filtering by material, room, cabinet number/range.
- Options for finish part size vs. cut size (accounting for edge banding).
- Custom Cutlist Editor: control columns, sorting, filtering, formatting.
- Automatic BOM / BOQ, hardware requirements, pricing, and quotes that update with the design.
- Export and print for shop or suppliers.
- Parts library allows customization of report names, labels, CNC eligibility, labor times.

## Nesting and Material Optimization
- Optimizer (in Manufacturing+ or CNC versions) analyzes the cut list and generates efficient sheet layouts to minimize waste.
- True-shape nesting for CNC.
- View nested sheets in 3D with operations displayed for verification.
- Support for remnants, spoilboard resurfacing, onion skinning, tabs, etc.
- Batch or per-sheet processing.

## Joinery and Construction Methods
- Customizable construction parameters and joinery rules.
- Support for dowels, dados, qualified tenons, knock-down fasteners, screws, confirmats, and combinations.
- Frameless vs. Face Frame styles.
- Automatic hardware boring (hinges, slides, handles) based on brand/model.
- Methods switch and adapt parts/machining automatically.
- CNC joint fasteners and automatic placement.

## Manufacturing Outputs
- Dimensioned drawings, shop drawings, assembly sheets, multiprint presentations.
- For CNC: machine-ready G-code with post-processors for many routers, drill-and-dowel machines, etc.
- Nested labels (NBM Labels), barcodes, paperless shop support.
- Exports for beam saws (CSV), single-part machines.
- Hardware lists, material requirements.

## Key Takeaways for PyModeler
- Cut list / part list generation is a high-value manufacturing helper (even early).
- Parts should carry material, size, thickness, edge banding, and manufacturing metadata.
- Simple nesting concepts and BOM generation belong in the roadmap.
- Joinery rules and automatic machining (boring, etc.) are domain-specific but useful for furniture/panel work.
- Keep manufacturing usefulness in mind from the start (clear part definitions, parameters that affect cut sizes).
- G-code / toolpath stubs are a longer-term goal; start with cut lists and drawings.

## References
- Mozaik Software product pages (Manufacturing, CNC, Enterprise)
- Mozaik Support: Cutlist Tab Customer Guide, Part Library
- Industry comparisons of cabinet design-to-manufacture software
