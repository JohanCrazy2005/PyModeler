# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Phase 4: True solid-of-revolution mesh from profile points for Revolve (Y-axis lathe, partial angles with caps) is now implemented; next is through-all extents for Hole or basic mesh bevel for Fillet/Chamfer.**

- RevolveFeature.generate_mesh now builds rings of vertices from polygon profile points (radial |x|, height y) and connects them into a closed surface of revolution.
- Partial angles add end-cap faces.
- Tests verify vertex counts and basic validity.
- Fallback to cylinder for non-polygon profiles remains.

### Next concrete tasks (Phase 4)
1. Through-all / to-face extents for Hole (or depth relative to body).
2. Basic mesh bevel approximation for Fillet / Chamfer on selected edges.
3. Use hole profiles in Extrude mesh generation (subtract holes).
4. Arbitrary axis support for Revolve (rotation matrix from given axis vector).
5. Constraint-aware sketch updates when applying transform intent.
6. Early sheet-metal / panel thinking or nesting concepts.
7. Two-distance or distance-angle modes for Chamfer.

## Recently Completed
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
