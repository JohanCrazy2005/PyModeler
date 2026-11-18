# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Viewport polish complete (Phase 3 increment).**

- RGB world axes (separate colored draws).
- Shading mode cycle: solid / wireframe / solid_wire (edges overlay).
- Standard views (front/right/top/etc.) + orthographic toggle.
- Keyboard shortcuts: F/. frame selected, A/Home frame all, 1/3/7 standard views, 5 ortho, G/R/S gizmo modes.
- Selection improvement: empty click clears selection.
- Tests updated and covering the new camera/shading APIs.

### Next concrete tasks (Phase 3 / Phase 2 remainder)
1. Optional UI exposure of mates, BOM, and grouped cut-list / CSV export.
2. Optional richer mate solver (rotation composition, revolute/slider stubs).
3. Configurations (independent inputs).
4. Further viewport: selection outline, better gizmo arrowheads, multi-select.

## Recently Completed
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
