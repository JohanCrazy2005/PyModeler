# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4: Through-all extent for Hole is implemented; next is basic mesh bevel approximation for Fillet/Chamfer or hole profiles in Extrude.**

- HoleFeature now supports `extent`: `"blind"` (default, uses `depth`) or `"through_all"`.
- Through-all generates a long centered tool cylinder (`through_depth` or default 1000) so Boolean cut fully pierces the body.
- Schema updated: `extent`, optional `through_depth`; `depth` no longer strictly required.
- Tests cover default through depth, explicit/parameterized through_depth, blind positioning, and schema round-trip.

### Next concrete tasks (Phase 4)
1. Basic mesh bevel approximation for Fillet / Chamfer on selected edges.
2. Use hole profiles in Extrude mesh generation (subtract holes).
3. Arbitrary axis support for Revolve (rotation matrix from given axis vector).
4. Constraint-aware sketch updates when applying transform intent.
5. Early sheet-metal / panel thinking or nesting concepts.
6. Two-distance or distance-angle modes for Chamfer.
7. Direction vector applied to Hole tool orientation (currently Y-axis + center offset only).

## Recently Completed
- Through-all / blind extents for Hole (schema + centered long tool mesh + tests)
- True solid-of-revolution mesh from profile points for Revolve (Y-axis, partial angle caps)
- Profile extraction: nested holes / outer+inner regions via point-in-polygon containment
- Profile extraction: proper arc joining into closed loops (discretize + insert into polygon)
- Chamfer feature stub (schema + distance/edges + placeholder mesh + history + tests)
- Fillet feature stub (schema + radius/edges + placeholder mesh + history + tests)
- Hole feature counterbore/countersink stubs (schema + tool mesh variants)
- Hole feature Boolean cut integration (Part.recompute respects operation=cut and applies mesh_boolean difference)
- Hole feature stub (schema + cylinder tool mesh + history + tests)
- Fixed Extrude symmetric mesh generation with start_offset
- Richer mate solver: matrix-based transform composition for rigid/fastened + revolute/slider stubs
- Scale + rotate parametric intent (points/radii/dimensions + plane origin)

## Notes for next agent
- Prefer small, complete, tested increments. Never break main.
- Always validate against JSON schemas in schemas/.
- Keep PyQt6, JSON Schemas, cross-platform public Python libs only.
- Put generated artifacts under output/ when appropriate.

Last updated: 2026-11-20 (Hole through-all extent + tests)
