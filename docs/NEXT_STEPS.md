# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Further gizmo polish and richer parametric intent (scale/rotate + constraints).**

- Translation gizmo now updates driving sketch plane origin + free points and recomputes the part (identity transform after).
- Next: better hit-testing on arrowheads/rings, visual feedback while dragging, and scale/rotate that can update simple driving parameters or dimensions.
- Keep headless-safe pure helpers.
- Main branch remains runnable (features.py restored).

### Next concrete tasks (Phase 3 / remaining)
1. Optional richer mate solver (rotation composition, revolute/slider stubs).
2. Further profile improvements (arcs properly joined into loops, holes, non-Y axis for revolve).
3. Gizmo polish: better hit-testing, drag feedback, scale/rotate parametric intent.
4. Constraint-aware sketch updates when applying transform intent.

## Recently Completed
- Parametric-intent translation: gizmo translate on current part offsets sketches and recomputes body
- Restored complete FeatureHistory / Extrude / Revolve implementation (was placeholder on main)
- Real solid-of-revolution mesh generation for RevolveFeature (profile points revolved around Y-axis, partial angle end-caps, circle bounding-box fallback)
- Richer gizmo visuals: arrowheads on translate axes, rotation rings for rotate mode, scale markers
- Selection outline / edge highlight overlay for selected objects + basic gizmo axes drawing
- Restored complete OpenGL paint path so transformed meshes are drawn
- Apply full transform (rotation + scale) in viewport mesh drawing / framing / picking
- UI panel for selecting and applying configuration values
- Restored core FeatureHistory data model (was placeholder)
- Assembly instance visualization in the viewport (transforms applied to SceneObjects)
- Configurations (independent inputs) schema + core + apply + tests
- UI exposure of mates, BOM, grouped cut-list, and CSV exports
- Viewport polish: RGB axes, shading modes, standard views, ortho toggle, keyboard nav, selection clear-on-miss
- Basic BOM generation: schema + aggregation from Parts or Assembly instances
- Assembly mates: rigid/fastened schema + basic location-offset solver
- Cut-list enhancements: grouping by material/thickness + CSV export helper
- Multi-part switching UI (parts list + switch + feature tree update)
- DXF export stub for 2D sketches and closed profiles (ezdxf)
- Simple Assembly container (schema + core data model + tests + research note)
- Light UI integration: MainWindow works with Part (FeatureTree, recompute body, cut-list display)
- Cut list / part list generation stub (schema + generator + tests)
- Material / stock definitions (schema + MaterialStore + default library)
- Multi-feature Part model (sketches + parameters + FeatureHistory → body mesh)

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
- Headless CI / sandbox lacks libEGL; keep pure-math and non-GL tests for viewport transform logic.
