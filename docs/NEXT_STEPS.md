# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority
Sketch data model foundation is complete (`schemas/sketch.schema.json` + `src/pymodeler/core/sketch.py` + tests). Next concrete work:

1. **Parameter system stub**
   - Create `schemas/parameter.schema.json` for user parameters / variables.
   - Implement `src/pymodeler/core/parameter.py` with a simple ParameterStore that can resolve named values.
   - Allow sketch dimensions to reference parameter names (already supported as string values).
   - Unit tests for store, resolution, and schema validation.

2. **Keep foundation solid**
   - Confirm all existing core tests pass.
   - Any small cleanups needed for main to stay runnable.

After parameters are in place and tested, the next increments will be:
- Basic Extrude feature (sketch profile → solid mesh or simple geometry), with parameter-driven distance.
- Feature history data model (timeline entries that store inputs).
- Timeline / feature tree UI stub.
- Initial 2D sketch editor widgets.

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
- Research documents for Fusion, Onshape, and Mozaik are in place; consult them before expanding Phase 1.
