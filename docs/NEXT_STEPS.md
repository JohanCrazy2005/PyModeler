# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Sketch data model foundation is complete and tested:
- `schemas/sketch.schema.json` aligned with core implementation
- `src/pymodeler/core/sketch.py` with entities, constraints, dimensions, rectangle factory
- Unit tests (9) all passing; symbols exported from `pymodeler.core`

Next concrete work:

1. **Parameter system stub**
   - Create `schemas/parameter.schema.json` for named user parameters (name, value, expression, unit optional).
   - Implement `src/pymodeler/core/parameters.py` with a ParameterStore that dimensions can reference by name.
   - Unit tests for create/update/evaluate (simple numeric + named refs) and schema round-trip.

2. **Keep foundation solid**
   - Confirm all existing tests pass.
   - Any small cleanups needed for main to stay runnable.

After Parameter system is in place and tested, the next increments will be:
- Basic Extrude feature (sketch profile → solid mesh or simple geometry) with parameter-driven distance
- Feature history data model (timeline of features)
- Timeline / feature tree UI stub
- Initial 2D sketch editor widgets

## Recently Completed
- Sketch JSON Schema (point, line, circle, arc; constraints; dimensions with numeric or parameter-name values)
- Sketch class with add_* helpers, create_rectangle_sketch, schema validation
- Tests for creation, constraints, dimensions, parameter refs, round-trip
- Core package exports updated

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
- Research documents for Fusion, Onshape, and Mozaik are now in place; consult them before expanding Phase 1.
