# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Simple Assembly data model is complete.**

- Schema: `schemas/assembly.schema.json` (instances with part_id + Transform).
- Core: `src/pymodeler/core/assembly.py` (`Assembly` + `Instance` classes, validation, add/remove, serialization).
- Research: `docs/research/assembly-model.md`.
- Tests: `tests/test_assembly.py` (all passing).
- Mates / constraint solving intentionally deferred.

### Next concrete tasks (Phase 2)
1. **DXF export stub** for 2D profiles / sketches using **ezdxf** (add to `src/pymodeler/io/`). Export closed profiles or sketch entities to DXF.
2. Multi-part switching UI (list of parts in MainWindow, switch `current_part`).
3. Optional cut-list enhancements: group by material/thickness, CSV export helper.
4. Later: Assembly mates schema + basic rigid/fastened mate solver.

## Recently Completed
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
