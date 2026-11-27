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
- Viewport picking further polish:
  - Multi-hit helpers `hit_test_edges_along_ray` / `hit_test_faces_along_ray` (sorted by distance).
  - Shift+click additive multi-select for edges/faces.
  - Basic box select (entities whose projected center is inside drag rect).
  - Select other: ` / ~ key cycles among last ray hits.
  - Mode keys: O (object), E (edge), T (face).
  - Green highlight overlay for selected edges / face boundaries.
  - Entity selection attributes properly initialized; signal `entity_selection_changed`.
- Tests for multi-hit helpers already present and now pass.

### Next concrete tasks (Phase 4)
1. Improve shell offset quality (true constant-thickness / openings via Boolean).
2. Further manufacturing drawing polish (dimension groups UI grouping, exact handle association).
3. Canvas badges further polish: proper SVG glyphs, in-place edit, drag badges to reposition.
4. Import/Export: basic STEP later if geometry kernel allows.

## Recently Completed
- Viewport picking further polish (multi-select, box, select-other, mode keys, highlight)
- Canvas badge related selection + hover highlight + dimension edit + full canvas restore
- Canvas badge polish (toggle, hover, double-click dimension edit)
- Canvas constraint + dimension badges
- Canvas multi-select + box select + restored working canvas
- 3-point arc mode (arc3) + RenderHint fix
- Arc mode full mouse interaction on canvas (3-click center/radius/end)
- Canvas mode toolbar wiring + dimension labels + midpoint snap
- Leader style UI control + export respect for ordinate/aligned
- Expanded sketch canvas drawing + basic interactivity
- Ordinate groups UI exposure + group_id/leader_style (prior)
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
- Canvas UI tests: use `QT_QPA_PLATFORM=offscreen` and ensure libEGL/libGL present on Linux CI.
- Known broad test failures outside sketch_canvas are pre-existing; this run only required green sketch_canvas + no new breakage in touched modules.
- Current HEAD previously had a truncated sketch_canvas.py; full implementation is restored.

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-27 (viewport picking further polish)
