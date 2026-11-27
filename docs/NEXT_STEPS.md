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
- Manufacturing drawing polish (dimension groups UI grouping + exact handle association):
  - Research note in `docs/research/manufacturing-drawings.md` (Fusion / Onshape / Inventor ordinate sets).
  - Sketch Editor: new "Add Ordinate Group" button – select ≥2 points, creates shared-origin ordinate set via `add_ordinate_group` (group_id + leader_style stamped).
  - Dimensions table: dedicated Group column; groups visible together.
  - DXF import matching: tighter default tolerance (0.5) on `_nearest_entity` for exact handle association.
  - Test: `test_sketch_editor_ordinate_group`.

### Next concrete tasks (Phase 4)
1. Canvas badges further polish: proper SVG glyphs, in-place edit, drag badges to reposition.
2. Import/Export: basic STEP later if geometry kernel allows.
3. Optional: shell rim walls after Boolean openings (currently openings only delete outer faces).
4. Further manufacturing drawing polish (group move-together behavior on canvas, origin indicator).

## Recently Completed
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

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-27 (manufacturing drawing polish – ordinate groups UI)
