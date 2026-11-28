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
- Shell openings now produce proper rim walls (not just face deletion).
  - Research updated in `docs/research/shell-boolean-offset.md`.
  - Wall-stitch path (and openings) adds connecting rim walls between outer and inner boundaries of removed faces.
  - Named face selectors (`top`/`bottom`/…) resolved by extreme centroid.
  - Restored full `ShellFeature` implementation in `shell_feature.py` (was a broken placeholder).
  - Volume on `create_cube(10)` inside t=1 still 488; opening test passes with extra rim faces.

### Next concrete tasks (Phase 4)
1. Import/Export: basic STEP later if geometry kernel allows.
2. Optional: more complex QtSvg icons if desired.
3. Further canvas polish (e.g., badge alignment snapping for ordinate leaders).
4. Optional: Boolean-path openings that also generate rim walls (currently openings use the wall-stitch path which already has rims).

## Recently Completed
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

Keep PLAN, CHECKLIST, and NEXT_STEPS synchronized after every significant run.

Last updated: 2026-11-27 (shell rim walls on openings)
