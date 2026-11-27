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
- Canvas constraint and dimension badges: simple text labels (H/V/C/= etc. for constraints, type:value for dimensions) placed near midpoints/centers with tooltips.
- Helpers `_draw_badges`, `_badge_position_for_entity`, `_add_badge` (data(1)="badge" for tests).
- Test: badge presence on rectangle sketch.

### Next concrete tasks (Phase 4)
1. Viewport picking further polish.
2. Improve shell offset quality (true constant-thickness / openings via Boolean).
3. Further manufacturing drawing polish (dimension groups UI grouping, exact handle association).
4. Import/Export: basic STEP later if geometry kernel allows.
5. Canvas constraint badges polish: glyphs, hover highlight, toggle visibility, double-click dimension edit.

## Recently Completed
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
- Canvas UI tests: use `QT_QPA_PLATFORM=offscreen` and ensure libEGL/libGL present on Linux CI.
- Known broad test failures outside sketch_canvas are pre-existing; this run only required green sketch_canvas + no new breakage in touched modules.

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-27 (canvas constraint and dimension badges)
