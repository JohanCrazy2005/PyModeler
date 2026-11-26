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
- Improved DIMENSION matching / angular recovery:
  - `_import_dimensions` now handles dimtype == 2 (2-line angular).
  - Pairs defpoint2/3 and defpoint4/5 (or available points) to match or create supporting lines.
  - Creates angle dimension with recovered measurement.
  - Tests extended (`tests/test_dxf_dims.py` — angular roundtrip).
  - Research note updated.

### Next concrete tasks (Phase 4)
1. Viewport picking further polish or multi-object entity selection.
2. Improve shell offset quality (true constant-thickness / openings via Boolean).
3. Further manufacturing drawing polish (dimension groups, leaders, etc.).
4. Import/Export: basic STEP later if geometry kernel allows.
5. Improved matching for other dimension variants / exact entity association.

## Recently Completed
- Improved DIMENSION matching / angular recovery (this run)
- Basic DIMENSION import recovery
- Ordinate + aligned DIMENSION export
- Better dimension placement (offset/side/angle + value-driven) 
- DXF diameter + angular DIMENSION export
- DXF DIMENSION export for length/radius
- DXF SPLINE/ELLIPSE approximation + TEXT stub
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
- Watch for files stored with literal `\\\\n` sequences — restore via unicode_escape if discovered.

Last updated: 2026-11-25 (angular DIMENSION import recovery)
