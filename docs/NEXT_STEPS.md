# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Assembly instance visualization in viewport complete.**

- MainWindow._show_assembly_in_viewport populates the scene with SceneObjects for each visible instance
- Applies the instance Transform (location / rotation / scale stored on SceneObject)
- Unique names, metadata with instance_id / part_id
- Automatically called after creating an assembly and after solving mates
- Manual menu action "Show Assembly in Viewport"
- Outliner and frame-all updated

### Next concrete tasks (Phase 3 / remaining)
1. Optional richer mate solver (rotation composition, revolute/slider stubs).
2. Further viewport: selection outline, better gizmo arrowheads, multi-select.
3. UI panel for selecting configuration values (list / numeric / boolean).
4. Apply full transform (rotation + scale) in viewport mesh drawing if not already done.

## Recently Completed
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
