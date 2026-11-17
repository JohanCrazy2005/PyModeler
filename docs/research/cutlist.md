# Cut List / Part List Generation

Research notes for Phase 2 manufacturing helpers. Last updated: 2026-11-17.

## Fusion 360 / Autodesk Fusion
- BOM and parts list from assemblies.
- Mass properties and material assignment feed into reports.
- Drawing views with dimensions; less emphasis on shop cut lists.

## Onshape
- BOM tables driven by assemblies and configurations.
- Custom properties on parts (material, finish, etc.).
- Exportable tables.

## Mozaik (manufacturing focus)
- Cut lists are first-class: generated from the design, grouped by material / thickness.
- Each entry shows quantity, part name, length × width × thickness (or size), material, edge banding, grain direction, CNC operations.
- Stock definitions drive what can be cut from which sheet.
- Part library entries carry manufacturing metadata that flows into the cut list.
- Output formats: printed lists, CSV, CNC-ready data.

## PyModeler design decisions (this increment)
- Schema: `schemas/cutlist.schema.json`
- Core: `src/pymodeler/core/cutlist.py`
  - `generate_cut_list(parts, material_store=None, quantities=None)` walks Parts, recomputes bodies, extracts AABB size (width/depth/height = dx/dy/dz), resolves material via MaterialStore.
  - `group_cut_list()` groups items by material, thickness, or material+thickness (Mozaik-style). Thickness prefers material.thickness else min bounding-box dimension.
  - `cut_list_to_csv()` and `cut_list_to_grouped_text()` helpers.
  - `CutList` wrapper exposes `groups()`, `to_csv()`, `to_grouped_text()`, `to_text()`.
- Quantity is a field on each item (not duplicated rows) so the document stays compact.
- Empty parts are included with `has_geometry: false` (size omitted).
- Next consumers: UI cut-list panel (with grouping/CSV export button), nesting concepts, BOM for assemblies.

## References
- Mozaik Cutlist documentation
- Onshape BOM / custom properties
- Fusion 360 BOM and drawing
