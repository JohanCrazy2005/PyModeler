# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4 polish + early manufacturing helpers.**

### Done this run
- Actually restored minimal SketchCanvasWidget (QGraphicsView stub) so SketchEditor imports and remains runnable (previous "restore" left the file empty).
- Confirmed ordinate group UI and full dimension types are present from prior commit.

### Next concrete tasks (Phase 4)
1. Leader style UI control (dropdown) + export respect for leader_style on ordinate/aligned dims.
2. Expand canvas drawing (points/lines/circles visual) now that the widget exists.
3. Viewport picking further polish or multi-object entity selection.
4. Improve shell offset quality (true constant-thickness / openings via Boolean).
5. Further manufacturing drawing polish (dimension groups UI grouping, exact handle association).
6. Import/Export: basic STEP later if geometry kernel allows.

## Recently Completed
- Ordinate groups UI exposure + group_id/leader_style (this run)
- Restored full DXF I/O module
- Multi-feature ordinate dimension groups (`add_ordinate_group`)
- Improved DIMENSION matching / angular recovery
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

## Notes for next agent
- Prefer small, complete, tested increments. Never break main.
- Always validate against JSON schemas in schemas/.
- Keep PyQt6, JSON Schemas, cross-platform public Python libs only.
- Put generated artifacts under output/ when appropriate.
- Pre-existing failures (materials schema drift, FeatureHistory.get_extrude_features, Part.get_body, occasional selection helper in sketch editor test) are known; do not expand scope to fix all of them unless the chosen task depends on them.
- `sketch_canvas.py` was empty on main; restored from eefbc97. Watch for empty-file regressions on push.

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-25 (canvas actually restored)
