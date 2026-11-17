# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Basic BOM generation complete.**

- Schema: `schemas/bom.schema.json`.
- Core: `src/pymodeler/core/bom.py` — `generate_bom` from Parts (with quantities) or from Assembly (instance counts by part_id).
- Aggregates unique part_ids, sums quantities, resolves materials via MaterialStore, includes optional AABB size.
- Helpers: `bom_to_text()`, `bom_to_csv()`. `BOM` wrapper with `from_parts` / `from_assembly`.
- Tests cover schema, parts path, assembly path, material resolution, CSV/text, and unresolved part_ids.
- Research note: `docs/research/bom.md`.

### Next concrete tasks (Phase 2 / 3)
1. Viewport polish / selection improvements (Phase 3).
2. Optional: UI exposure of mates, BOM, and grouped cut-list / CSV export.
3. Optional: richer mate solver (rotation composition, revolute/slider stubs).
4. Configurations (independent inputs).

## Recently Completed
- Basic BOM generation: schema + aggregation from Parts or Assembly instances
- Assembly mates: rigid/fastened schema + basic location-offset solver
- Cut-list enhancements: grouping by material/thickness + CSV export helper
- Multi-part switching UI (parts list + switch + feature tree update)
- DXF export stub for 2D sketches and closed profiles (ezdxf)
- Simple Assembly container (schema + core data model + tests + research note)
- Light UI integration: MainWindow works with Part (FeatureTree, recompute body, cut-list display)
- Cut list / part list generation stub (schema + generator + tests)
- Material / stock definitions (schema + MaterialStore + default library)
- Multi-feature Part model (sketches + parameters + FeatureHistory → body mesh)

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
