# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Revolve feature is complete and tested (schema + parameter-driven angle + simple solid-of-revolution mesh):
- `schemas/revolve.schema.json`
- `src/pymodeler/core/features.py` — RevolveFeature (angle numeric or parameter, optional axis, segments)
- Integrated into FeatureHistory (add_revolve, get_revolve_features, recompute_meshes)
- Research note in `docs/research/revolve-feature.md`
- Unit tests for the feature and history integration

Next concrete work:

1. **Improve sketch editor**
   - Editable table cells for point coordinates and dimension values
   - Better selection of entities when adding lines/dimensions

2. **Better profile support**
   - Extrude and Revolve should handle simple polygons and circles better
   - Arc support in profile extraction

3. Keep foundation solid; all existing tests must continue to pass.

After sketch editor improvements, next increments:
- Start offset / symmetric improvements for Extrude
- Boolean operations (join/cut) on generated meshes
- Rollback marker and feature reordering in the timeline
- Visual 2D canvas for sketching

## Recently Completed
- Revolve feature (schema, parameter-driven angle, faceted solid of revolution, FeatureHistory integration)
- Basic 2D sketch editor widgets (table-based) + research note
- Feature tree / timeline UI stub + property panel for Extrude features
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
