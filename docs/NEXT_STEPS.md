# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority
Research phase for the parametric CAD goal is complete. Next concrete work:

1. **Sketch data model foundation**
   - Create `schemas/sketch.schema.json` defining entities (point, line, circle, arc, rectangle…), constraints (coincident, horizontal, parallel, tangent, equal…), and dimensions.
   - Implement `src/pymodeler/core/sketch.py` with classes that validate against the schema.
   - Add unit tests for creation, constraint application, and schema round-trip.

2. **Parameter system stub**
   - Schema + simple Parameter / Variable store that dimensions can reference.

3. **Keep foundation solid**
   - Confirm all existing tests pass.
   - Any small cleanups needed for main to stay runnable.

After sketch schema + core model are in place and tested, the next increments will be:
- Basic Extrude feature (sketch profile → solid mesh or simple geometry)
- Feature history data model
- Timeline / feature tree UI stub
- Initial 2D sketch editor widgets

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
- Research documents for Fusion, Onshape, and Mozaik are now in place; consult them before expanding Phase 1.
