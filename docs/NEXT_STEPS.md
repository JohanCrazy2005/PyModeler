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
- DXF import: SPLINE / ELLIPSE approximation + TEXT stub (Phase 4):
  - `import_dxf_to_sketch` now accepts SPLINE and ELLIPSE (flattened to LINE polylines via `flattening(distance=0.1)` or path fallback).
  - TEXT entities create a point at insert location; content stored in `sketch.metadata["imported_texts"]`.
  - Research in `docs/research/dxf-additional-entities.md`. New tests in `tests/test_dxf.py` (all pass).

### Next concrete tasks (Phase 4)
1. Import/Export: basic STEP later if geometry kernel allows.
2. Viewport picking further polish or multi-object entity selection.
3. Improve shell offset quality (true constant-thickness / openings via Boolean).
4. Dimension export (DIMENSION entities from sketch dimensions).

## Recently Completed
- DXF SPLINE/ELLIPSE approximation + TEXT stub (this run)
- Boolean-based shell offset for closed inside shells
- DXF bulge-aware polyline import
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

Last updated: 2026-11-24 (DXF SPLINE/ELLIPSE/TEXT import)
