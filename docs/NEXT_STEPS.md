# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4 Chamfer feature stub complete; next is profile improvements or basic mesh bevel.**

- ChamferFeature stub: JSON Schema (distance, edges list, operation=modify), parametric distance, placeholder cone mesh, FeatureHistory integration, tests.
- Research note: docs/research/chamfer-feature.md.
- Full mesh bevel chamfer deferred (mesh-based limitation). Equal-distance mode only for now.

### Next concrete tasks (Phase 4)
1. Further profile improvements: proper arc joining into loops, holes in profiles, non-Y axis for revolve.
2. Constraint-aware sketch updates when applying transform intent.
3. Early sheet-metal / panel thinking or nesting concepts.
4. Through-all / to-face extents for Hole.
5. Basic mesh bevel approximation for Fillet / Chamfer on selected edges.
6. Two-distance or distance-angle modes for Chamfer.

## Recently Completed
- Chamfer feature stub (schema + distance/edges + placeholder mesh + history + tests)
- Fillet feature stub (schema + radius/edges + placeholder mesh + history + tests)
- Hole feature counterbore/countersink stubs (schema + tool mesh variants)
- Hole feature Boolean cut integration (Part.recompute respects operation=cut and applies mesh_boolean difference)
- Hole feature stub (schema + cylinder tool mesh + history + tests)
- Fixed Extrude symmetric mesh generation with start_offset
- Richer mate solver: matrix-based transform composition for rigid/fastened + revolute/slider stubs
- Scale + rotate parametric intent (points/radii/dimensions + plane axes) on gizmo commit
- Gizmo polish: pure tip/ring/marker hit-testing + drag visual feedback (brighter active axis)
- Restored complete MainWindow (was empty on main) with parametric translation wiring
- Parametric-intent translation: gizmo translate on current part offsets sketches and recomputes the part
- Restored complete FeatureHistory / Extrude / Revolve implementation
- Real solid-of-revolution mesh generation for RevolveFeature
- Richer gizmo visuals: arrowheads, rotation rings, scale markers
- Selection outline / edge highlight overlay
- Full transform (rotation + scale) in viewport mesh drawing / framing / picking
- UI panel for selecting and applying configuration values
- Assembly instance visualization in the viewport
- Configurations (independent inputs)
- UI exposure of mates, BOM, grouped cut-list, and CSV exports
- Viewport polish: RGB axes, shading modes, standard views, ortho toggle, keyboard nav
- Basic BOM, Assembly mates, Cut-list enhancements, Multi-part switching UI
- DXF export stub, Simple Assembly, Material/stock, Multi-feature Part model

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows.
- Keep main branch runnable and tested. Small complete increments.
- Headless CI / sandbox lacks libEGL; keep pure-math and non-GL tests for viewport transform logic.
