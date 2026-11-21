# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4: Hole direction exposed in property panel. Next priorities below.**

### Done this run
- Extended FeatureTreeWidget to instantiate HoleFeature on selection.
- Extended PropertyPanel to display and edit HoleFeature:
  - Diameter (in distance field)
  - Depth (in offset/depth field)
  - Direction vector as "x,y,z" text field (optional)
- Apply path updates history dict and validates.
- Added test_property_panel_hole_direction covering show + edit of direction and diameter.

### Next concrete tasks (Phase 4)
1. Constraint-aware sketch updates when applying transform intent.
2. Improve bevel quality (better corner fans, optional manifold cleanup).
3. Early sheet-metal / panel thinking or nesting concepts.
4. Better shell: corner mitering, Boolean-based offset when engine available, or true face removal openings.
5. UI exposure for other Phase 4 features (fillet radius, chamfer mode, shell thickness/faces).

## Recently Completed
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
- Pre-existing failures (materials schema drift, FeatureHistory.get_extrude_features, SketchCanvasWidget import) are unrelated; do not expand scope unless fixing them is the chosen task.

Last updated: 2026-11-20 (Hole direction UI)
