# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4 polish + better bevel quality. Next priorities below.**

### Done this run
- Improved `Mesh.bevel_edges` quality:
  - Offsets now use adjacent-face average normals and a true perpendicular direction instead of fixed world-axis offsets.
  - Adds proper chamfer quads.
  - Multi-segment path inserts intermediate vertices for a coarser fillet approximation.
  - Vertices where multiple beveled edges meet receive simple corner fans (triangles from the original vertex).
  - Optional `cleanup=True` (default) merges near-coincident vertices and drops degenerate faces.
- Added a focused test verifying corner fans + cleanup still produce a valid mesh with increased face count.
- Existing bevel / fillet / chamfer apply tests continue to pass (pre-existing Part.get_body failures remain unrelated).

### Next concrete tasks (Phase 4)
1. Early sheet-metal / panel thinking or nesting concepts (research + schema stub).
2. Better shell: corner mitering, Boolean-based offset when engine available, or true face removal openings.
3. UI exposure for edges/faces selection on Fillet/Chamfer/Shell (or other remaining Phase 4 polish).
4. Further constraint propagation (e.g., equal lengths, horizontal/vertical under non-uniform scale) or a lightweight solver stub.
5. Optional: more robust manifold repair / Boolean bevel when manifold3d is present.

## Recently Completed
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

Last updated: 2026-11-21 (Improved bevel quality)
