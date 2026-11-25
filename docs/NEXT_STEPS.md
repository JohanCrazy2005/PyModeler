# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4 polish + early manufacturing helpers. Next priorities below.**

### Done this run
- DXF import improvements (Phase 4):
  - `import_dxf_to_sketch` now handles `LWPOLYLINE` and legacy `POLYLINE`.
  - Bulge values expanded via `virtual_entities()` into real ARC entities (straight segments stay LINE).
  - Research note appended to `docs/research/dxf-export.md`. New tests for bulge and POLYLINE. Tests pass.

### Next concrete tasks (Phase 4)
1. Optional Boolean-based shell offset when engine (manifold3d) available.
2. More DXF entities (SPLINE approximation, ELLIPSE, TEXT stubs) or dimension export.
3. Import/Export: basic STEP later if geometry kernel allows.
4. Viewport picking further polish or multi-object entity selection.

## Recently Completed
- DXF bulge-aware polyline import (this run)
- Viewport picking polish (multi-select, highlight, box, select-other)
- True Archimedean + morphing spiral toolpaths
- Robust manifold repair
- Better shell openings
- Full unit system with suffixes
- ... (prior items retained in history)

## Notes for next agent
- Prefer small, complete, tested increments. Never break main.
- Always validate against JSON schemas in schemas/.
- Keep PyQt6, JSON Schemas, cross-platform public Python libs only.
- Put generated artifacts under output/ when appropriate.
- Pre-existing failures (materials schema drift, FeatureHistory.get_extrude_features, SketchCanvasWidget import, Part.get_body) are unrelated; do not expand scope unless fixing them is the chosen task.
- Headless environments may lack libEGL; UI widget tests that need a display can be skipped or guarded.

Last updated: 2026-11-24 (DXF bulge-aware import)
