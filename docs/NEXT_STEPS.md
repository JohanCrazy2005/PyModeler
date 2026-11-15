# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Parameter system is complete and tested:
- `schemas/parameter.schema.json` (name, value, expression, unit, comment)
- `src/pymodeler/core/parameters.py` — ParameterStore with create/update/evaluate (numeric + named refs + basic arithmetic)
- Research note in `docs/research/parameters-variables.md`
- 8 unit tests passing; symbols exported from `pymodeler.core`

Next concrete work:

1. **Basic Extrude feature**
   - Schema for Extrude feature (profile sketch reference + distance parameter or numeric)
   - Implementation that produces a simple solid (mesh or parametric solid stub) driven by a sketch + distance parameter
   - Unit tests for creation, parameter-driven distance, schema round-trip

2. **Feature history data model**
   - Timeline of features (sketch → extrude → …) that can be serialized and recomputed

3. Keep foundation solid; all existing tests must continue to pass.

After Extrude + history stubs, next increments:
- Timeline / feature tree UI stub
- Initial 2D sketch editor widgets
- Revolve feature

## Recently Completed
- ParameterStore + JSON Schema + expression evaluation (simple arithmetic + named refs)
- Research notes for parameters/variables in Fusion, Onshape, Mozaik
- Sketch JSON Schema + core data model (entities, constraints, dimensions)
- Core package exports updated

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
- Research documents for Fusion, Onshape, and Mozaik are in place; consult them before expanding Phase 1.
