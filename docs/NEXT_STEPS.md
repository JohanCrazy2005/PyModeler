# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Multi-feature Part model is complete.**

A `Part` now owns:
- sketches (dict)
- ParameterStore
- FeatureHistory
- optional material
- `recompute()` that sequentially joins feature meshes into a single body Mesh

Schema: `schemas/part.schema.json`
Core: `src/pymodeler/core/part.py`
Tests: `tests/test_part.py`

### Next concrete tasks (Phase 2)
1. **Material / stock definitions** (schema + simple store) so Parts can carry manufacturing-relevant data.
2. **Cut list / part list generation stub** that walks one or more Parts and emits quantity, size, material.
3. Light UI integration: MainWindow holds a Part (or list of Parts); FeatureTree already works with FeatureHistory.
4. Begin simple Assembly container (references to Parts + basic mates later).

## Recently Completed
- Part model (sketches + parameters + FeatureHistory → body mesh)
- Research note: docs/research/part-model.md
- Restored working sketch.py from history (previous placeholder breakage)

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
