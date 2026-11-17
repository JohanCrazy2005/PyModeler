# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**DXF export stub is complete.**

- Module: `src/pymodeler/io/dxf.py` (`export_sketch_to_dxf`, `export_profiles_to_dxf`).
- Uses **ezdxf** to write lines, circles, arcs, and closed profiles (LWPOLYLINE) from Sketch / `extract_simple_profiles`.
- Tests: `tests/test_dxf.py` (all passing).
- Research note: `docs/research/dxf-export.md`.

### Next concrete tasks (Phase 2)
1. **Multi-part switching UI** in MainWindow (list of parts, switch `current_part`, feature tree updates).
2. Optional cut-list enhancements: group by material/thickness, CSV export helper.
3. Later: Assembly mates schema + basic rigid/fastened mate solver.
4. Viewport polish / selection improvements.

## Recently Completed
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
