# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Material / stock definitions are complete.**

- Schema: `schemas/material.schema.json`
- Core: `src/pymodeler/core/material.py` (`MaterialStore`, validation, default library)
- Tests: `tests/test_material.py`
- Research: `docs/research/material-stock.md`
- Part continues to accept material as string or object (no breaking change)

### Next concrete tasks (Phase 2)
1. **Cut list / part list generation stub** that walks one or more Parts and emits quantity, size, material (use MaterialStore when material is an id/name).
2. Light UI integration: MainWindow holds a Part (or list of Parts); FeatureTree already works with FeatureHistory; optional material property display.
3. Begin simple Assembly container (references to Parts + basic transforms; mates later).
4. DXF export stub for 2D profiles using ezdxf (when dependency is added).

## Recently Completed
- Material / stock definitions (schema + MaterialStore + default library)
- Multi-feature Part model (sketches + parameters + FeatureHistory → body mesh)
- Research note: docs/research/part-model.md, docs/research/material-stock.md
- Restored working sketch.py from history (previous placeholder breakage)

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
