# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4: Basic mesh bevel for Fillet/Chamfer is implemented. Next priorities below.**

### Done this run
- `Mesh.get_unique_edges()`, `Mesh.edge_face_map()`, `Mesh.bevel_edges(edges, amount, segments)` — basic equal-distance edge bevel.
- segments=1 → flat chamfer; segments>1 → multi-cut fillet approximation.
- `ChamferFeature.apply_to_mesh` / `FilletFeature.apply_to_mesh` call bevel_edges.
- Default `operation` fixed to `"modify"` (was invalid `"join"` vs schema enum).
- `Part.recompute` applies fillet/chamfer as in-place mesh modifications on the current body.
- 16 new tests in `tests/test_bevel.py` (all passing).

### Next concrete tasks (Phase 4)
1. Use hole profiles in Extrude mesh generation (subtract nested holes from profiles).
2. Arbitrary axis support for Revolve (rotation matrix from given axis vector).
3. Two-distance or distance-angle modes for Chamfer (schema + apply path).
4. Direction vector applied to Hole tool orientation (currently Y-axis + center offset only).
5. Constraint-aware sketch updates when applying transform intent.
6. Improve bevel quality (better corner fans, optional manifold cleanup).
7. Early sheet-metal / panel thinking or nesting concepts.
8. Shell feature stub.

## Recently Completed
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

Last updated: 2026-11-20 (Mesh bevel for Fillet/Chamfer)
