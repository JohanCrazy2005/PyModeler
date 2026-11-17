# Basic Bill of Materials (BOM)

Research notes for Phase 2 manufacturing helpers. Last updated: 2026-11-17.

## Fusion 360 / Autodesk Fusion
- BOM generated from assemblies (or multi-body parts).
- Lists components with quantities, part numbers, descriptions, materials, mass properties.
- Can include custom properties; exportable to CSV / used in drawings.
- Updates when the design changes.

## Onshape
- Assembly-driven BOM tables.
- Custom properties on parts (material, finish, vendor, cost, etc.).
- Configurable columns; export to CSV.
- Supports configurations and suppressed instances.

## Mozaik
- Automatic BOM / BOQ alongside cut lists.
- Includes hardware, materials, and labor items that update with the design.
- Used for quotes, purchasing, and shop reports.
- Parts library carries the metadata that flows into the BOM.

## PyModeler design decisions (this increment)
- Schema: `schemas/bom.schema.json` (parallel to cutlist but focused on unique parts + quantities).
- Core: `src/pymodeler/core/bom.py`
  - `generate_bom(parts=None, assembly=None, parts_map=None, material_store=None, quantities=None)`
  - From a list of Parts + optional quantities dict, or from an Assembly (counts instances by part_id, resolves Part objects via parts_map or Instance.part).
  - Aggregates by part_id: summed quantity, resolved material name/id, optional bounding-box size of the recomputed body.
  - Helpers: `bom_to_text()`, `bom_to_csv()`.
  - `BOM` wrapper class.
- Quantity is summed for duplicate part_ids so the document stays compact.
- Empty / unresolved parts are included with `has_geometry: false`.
- Fully schema-validated; backward-compatible with existing Part/Assembly data.
- Next consumers: UI BOM panel, CSV export button, integration with cut-list view, later cost/hardware columns.

## References
- Onshape BOM documentation
- Fusion 360 BOM / parts list
- Mozaik automatic BOM / BOQ
