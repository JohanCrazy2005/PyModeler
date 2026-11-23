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
- Completed nesting-from-parts wiring (was partially committed):
  - Added missing `nesting_job_from_parts` + `DEFAULT_SHEET_SIZES` in core/nesting.py so core import no longer breaks.
  - Manufacturing menu: "Nesting Preview…" builds job from current parts (sample fallback when no geometry) and shows NestingPreviewDialog.
  - "Cut List" menu now shows real generated text.
  - Tests cover geometry path, fallback sample, no-fallback empty, and the constant.

### Next concrete tasks (Phase 4)
1. Toolpath UI preview: simple dialog showing generated G-code text + optional 2D path plot (QPainter).
   (or spiral continuous single-path / Archimedean refinement).
2. Optional: more robust manifold repair / Boolean bevel when manifold3d is present.
3. Better shell openings (explicit rim walls, non-integer face ids) or Boolean-based offset when engine available.
4. Viewport-based edge/face picking for Fillet/Chamfer/Shell (beyond text entry).
5. Full unit system with suffixes in expressions (e.g. `2 in + 10 mm`) or more conversion helpers.
6. Import/Export improvements (DXF via ezdxf already present; STEP later if geometry kernel allows).

## Recently Completed
- Nesting UI preview widget + dialog (QPainter sheet layouts)
- Nesting multi-sheet-size selection (smallest fitting sheet preferred)
- Wire nesting preview to real cut-list / current part data (`nesting_job_from_parts`)
- Toolpath spiral pocket strategy
- Circular arcs / corner radius for rectangular toolpaths (G03)
- Linear lead-in / lead-out for toolpaths (optional lengths)
- Trig / unit-aware functions in expression evaluator (sin/cos degrees, sqrt, pi, in_to_mm, ...)
- Full arithmetic expression evaluation for dimension values in constraint solver
- Parameter evaluation for dimension values (string parameter name refs) in constraint solver
- Driving dimensions (length/distance/radius/diameter/angle) + free radii in constraint solver
- Lightweight 2D constraint solver stub (scipy least_squares)
- UI exposure for edges/faces selection on Fillet/Chamfer/Shell (property panel text field)
- Shell corner mitering (scale-adjusted normal offset)
- Toolpath polish – zig-zag pocket strategy
- Early toolpath / G-code generation stubs (ToolpathJob schema + rectangular pocket & contour + research)
- Rectangular NestingJob schema + shelf packer + from-cutlist helper + research
- Sheet-metal rule schema + bend-allowance helper + research
- Improved bevel quality (normal-based offsets, corner fans, optional cleanup)
- Constraint-aware sketch updates when applying transform intent (locked points + coincident components)
- UI exposure for Fillet radius, Chamfer mode/distance/secondary, Shell thickness/direction (property panel)
- UI exposure for hole direction (property panel)
- Shell basic mesh approximation (normal offset + walls + openings)
- Shell feature stub (schema, history, placeholder mesh)
- Direction vector applied to Hole tool orientation (Rodrigues rotation from Y-axis)
- Two-distance / distance-angle modes for Chamfer (schema + apply path + basic bevel)
- Arbitrary axis support for Revolve (Rodrigues rotation from Y-axis to given axis vector + origin)
- Hole profiles used in Extrude mesh generation (Boolean cut + pure wall fallback + test)
- Basic mesh bevel approximation for Fillet / Chamfer (Mesh.bevel_edges + apply_to_mesh + Part.recompute modify path + tests)

## Notes for next agent
- Prefer small, complete, tested increments. Never break main.
- Always validate against JSON schemas in schemas/.
- Keep PyQt6, JSON Schemas, cross-platform public Python libs only.
- Put generated artifacts under output/ when appropriate.
- Pre-existing failures (materials schema drift, FeatureHistory.get_extrude_features, SketchCanvasWidget import, Part.get_body) are unrelated; do not expand scope unless fixing them is the chosen task.
- Headless environments may lack libEGL; UI widget tests that need a display can be skipped or guarded.

Last updated: 2026-11-23 (complete nesting-from-parts wiring + menu)
