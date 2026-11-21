# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4: Shell basic mesh approximation implemented. Next priorities below.**

### Done this run
- Researched and documented Shell (already present).
- Implemented basic mesh shell approximation in ShellFeature.apply_to_mesh:
  - Offset vertices along averaged face normals by thickness.
  - Build outer + inner (reversed) surfaces + connecting wall faces.
  - Integer face indices treated as openings (omitted).
  - Directions: inside / outside / both.
- Integrated into Part.recompute modify path.
- Updated tests: shell now produces more geometry; opening reduces face count.
- Schema and research note updated.

### Next concrete tasks (Phase 4)
1. Constraint-aware sketch updates when applying transform intent.
2. Improve bevel quality (better corner fans, optional manifold cleanup).
3. Early sheet-metal / panel thinking or nesting concepts.
4. UI exposure for hole direction (property panel or sketch normal picker).
5. Better shell: corner mitering, Boolean-based offset when engine available, or true face removal openings.

## Recently Completed
- Shell basic mesh approximation (normal offset + walls + openings)
- Shell feature stub (schema, history, placeholder mesh)
- Direction vector applied to Hole tool orientation (Rodrigues rotation from Y-axis)
- Two-distance / distance-angle modes for Chamfer (schema + apply path + basic bevel)
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

Last updated: 2026-11-20 (Shell basic mesh approximation)
