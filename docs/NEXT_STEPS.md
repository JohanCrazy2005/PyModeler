# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Feature tree / timeline UI stub is complete and tested (core path):
- `src/pymodeler/ui/feature_tree.py` — FeatureTreeWidget (lists ExtrudeFeatures) + PropertyPanel (name + distance editor)
- Integrated into MainWindow (left: outliner + timeline, right: properties)
- Research note in `docs/research/feature-tree-ui.md`
- Unit tests for the widgets (Qt-dependent environment may need EGL libs)

Next concrete work:

1. **Basic 2D sketch editor widgets**
   - Simple canvas or table-based editor to create/edit sketch entities and dimensions
   - Connect to Sketch data model and FeatureHistory

2. **Revolve feature**
   - Schema + implementation analogous to Extrude (profile + axis + angle)
   - Research note first

3. Keep foundation solid; all existing tests must continue to pass.

After sketch editor stubs, next increments:
- Better profile support in Extrude (arcs, circles)
- Start offset / symmetric improvements
- Boolean operations (join/cut) on generated meshes
- Rollback marker and feature reordering in the timeline

## Recently Completed
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
