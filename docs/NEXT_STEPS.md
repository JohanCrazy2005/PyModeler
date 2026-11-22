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
- Shell corner mitering:
  - Updated `ShellFeature.apply_to_mesh` to compute a per-vertex miter scale (average of 1/(vn·nf) over adjacent faces, clamped).
  - Offset vertices by thickness * scale * vertex_normal so wall thickness is more uniform at sharp corners.
  - Docstring updated. New test `test_shell_mitered_corners` verifies larger corner displacement on a cube (all tests pass).

### Next concrete tasks (Phase 4)
1. UI exposure for edges/faces selection on Fillet/Chamfer/Shell (or other remaining Phase 4 polish).
2. Further constraint propagation (e.g., equal lengths, horizontal/vertical under non-uniform scale) or a lightweight solver stub.
3. Optional: more robust manifold repair / Boolean bevel when manifold3d is present.
4. Nesting polish: multi-sheet-size selection, remnant tracking, or simple UI preview of layouts.
5. Further toolpath polish: lead-in/out, circular arcs (G02/G03), or UI preview of generated G-code.
6. Better shell openings (explicit rim walls, non-integer face ids) or Boolean-based offset when engine available.

## Recently Completed
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

Last updated: 2026-11-22 (Shell corner mitering)
