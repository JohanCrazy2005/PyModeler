# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4: Arbitrary axis for Revolve is implemented. Next priorities below.**

### Done this run
- `ExtrudeFeature.generate_mesh` now consumes nested holes from `extract_simple_profiles`.
- `_extrude_polygon_with_holes` attempts a true Boolean cut (via `mesh_boolean`) when an engine is present.
- Pure-Python fallback `_extrude_walls_with_holes` builds outer + reversed inner walls so holes are geometrically present even without manifold3d.
- New test `test_extrude_with_nested_holes` (passes).

### Next concrete tasks (Phase 4)
1. Two-distance or distance-angle modes for Chamfer (schema + apply path).
2. Direction vector applied to Hole tool orientation (currently Y-axis + center offset only).
3. Constraint-aware sketch updates when applying transform intent.
4. Improve bevel quality (better corner fans, optional manifold cleanup).
5. Early sheet-metal / panel thinking or nesting concepts.
6. Shell feature stub.

## Recently Completed
- Arbitrary axis support for Revolve (Rodrigues rotation from Y-axis to given axis vector + origin)
- Hole profiles used in Extrude mesh generation (Boolean cut + pure wall fallback + test)
- Basic mesh bevel approximation for Fillet / Chamfer (Mesh.bevel_edges + apply_to_mesh + Part.recompute modify path + tests)
- Fixed Fillet/Chamfer operation default to schema-valid `"modify"`
- Through-all / blind extents for Hole
- True solid-of-revolution mesh from profile points for Revolve (Y-axis, partial angle caps)
- Profile extraction: nested holes / outer+inner regions via point-in-polygon containment
- Profile extraction: proper arc joining into closed loops
- Chamfer / Fillet feature stubs (schema + history)
- Hole feature Boolean cut integration
- Richer mate solver + parametric transform intent

## Notes for next agent
- Prefer small, complete, tested increments. Never break main.
- Always validate against JSON schemas in schemas/.
- Keep PyQt6, JSON Schemas, cross-platform public Python libs only.
- Put generated artifacts under output/ when appropriate.
- Pre-existing failures (materials schema drift, FeatureHistory.get_extrude_features, SketchCanvasWidget import) are unrelated; do not expand scope unless fixing them is the chosen task.

Last updated: 2026-11-20 (Extrude hole profiles)
