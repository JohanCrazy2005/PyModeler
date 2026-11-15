# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Extrude feature and FeatureHistory are complete and tested:
- `schemas/extrude.schema.json` + `schemas/feature_history.schema.json`
- `src/pymodeler/core/features.py` — ExtrudeFeature (sketch + numeric/parameter distance → solid mesh) and FeatureHistory (timeline + recompute)
- Research note in `docs/research/extrude-feature.md`
- Unit tests passing; symbols exported from `pymodeler.core`

Next concrete work:

1. **Timeline / feature tree UI stub**
   - PyQt6 tree or list that displays FeatureHistory and allows selecting features
   - Property panel that shows Extrude distance (and allows editing parameter references)

2. **Basic 2D sketch editor widgets**
   - Simple canvas or table-based editor to create/edit sketch entities and dimensions

3. **Revolve feature**
   - Schema + implementation analogous to Extrude (profile + axis + angle)

4. Keep foundation solid; all existing tests must continue to pass.

After UI stubs, next increments:
- Better profile support in Extrude (arcs, circles)
- Start offset / symmetric improvements
- Boolean operations (join/cut) on generated meshes

## Recently Completed
- ExtrudeFeature + FeatureHistory (schema, parameter-driven distance, mesh generation, recompute)
- Research notes for parametric Extrude in Fusion 360 and Onshape
- ParameterStore + JSON Schema + expression evaluation
- Sketch JSON Schema + core data model

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
- Research documents for Fusion, Onshape, and Mozaik are in place; consult them before expanding Phase 1.
