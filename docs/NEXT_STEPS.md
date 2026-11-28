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
- Canvas dimension leader line visualization.
  - Research notes updated in `docs/research/sketch-canvas-badges.md`.
  - `_draw_dimension_leaders` draws thin dashed leaders from dimension badges to geometry.
  - Ordinate leaders are axis-aligned (horizontal/vertical segments) to match badge snapping.
  - Other dimensions get a simple straight leader.
  - Leader items tagged `data(1)="leader"` for tests.
  - Test `test_dimension_leader_lines_drawn` verifies presence and ordinate alignment.

### Next concrete tasks (Phase 4)
1. Import/Export: basic STEP later if geometry kernel allows.
2. Optional: more complex QtSvg icons if desired.
3. Optional: Boolean-path openings that also generate rim walls (currently openings use the wall-stitch path which already has rims).
4. Further canvas polish (e.g., extension lines for linear dimensions, arrowheads on leaders).

## Recently Completed
- Dimension leader line visualization on canvas
- Ordinate badge alignment snapping (axis-aligned + group mate)
- Shell openings produce rim walls + restored full ShellFeature
- Ordinate group move-together + origin indicator on canvas
- True vector SVG-style glyphs for constraint badges
- Canvas badge polish (drag-to-reposition + in-place dimension edit)
- Manufacturing drawing polish (ordinate group UI + tighter entity association)
- Shell constant-thickness Boolean offset + openings
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
- Boolean-based shell offset for closed inside shells (centroid scale — superseded)
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
- Known broad test failures outside the touched modules are pre-existing.
- Shell Boolean path requires `trimesh` + `manifold3d`; without them wall-stitch still works.
- Note: `src/pymodeler/render/viewport.py` currently contains a placeholder string on main; do not let that block canvas work.

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-27 (dimension leader line visualization)
