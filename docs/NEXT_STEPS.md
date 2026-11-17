# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Cut-list / part-list generation stub is complete.**

- Schema: `schemas/cutlist.schema.json`
- Core: `src/pymodeler/core/cutlist.py` (`generate_cut_list`, `CutList`, text formatter)
- Tests: `tests/test_cutlist.py`
- Research: `docs/research/cutlist.md`
- Walks Parts → quantity, AABB size, resolved material (via MaterialStore)

### Next concrete tasks (Phase 2)
1. **Light UI integration**: MainWindow holds one or more Parts; FeatureTree works with a Part’s FeatureHistory; optional material / cut-list property display or simple panel.
2. Begin simple Assembly container (references to Parts + basic transforms; mates later).
3. DXF export stub for 2D profiles using ezdxf (when dependency is added).
4. Optional: group cut-list items by material / thickness; CSV export helper.

## Recently Completed
- Cut list / part list generation stub (schema + generator + tests)
- Material / stock definitions (schema + MaterialStore + default library)
- Multi-feature Part model (sketches + parameters + FeatureHistory → body mesh)
- Research note: docs/research/part-model.md, docs/research/material-stock.md, docs/research/cutlist.md
- Restored working sketch.py from history (previous placeholder breakage)

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
