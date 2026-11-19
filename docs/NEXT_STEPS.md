# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Further profile improvements + start Phase 4 feature stubs.**

- Mate solver now uses full matrix composition for rigid/fastened (correct rotation composition) and accepts revolute/slider as stubs that apply the fixed offset.
- Next: improve closed-profile extraction (proper arc joining into loops, holes) and begin a simple Fillet or Hole feature.

### Next concrete tasks (Phase 3 remaining / Phase 4 start)
1. Further profile improvements (arcs properly joined into loops, holes, non-Y axis for revolve).
2. Constraint-aware sketch updates when applying transform intent (respect fixed/constrained points better).
3. Begin Phase 4: simple Fillet or Hole feature stub (schema + basic mesh generation).
4. Optional: richer DOF handling for revolute/slider (axis + limits stubs).

## Recently Completed
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
