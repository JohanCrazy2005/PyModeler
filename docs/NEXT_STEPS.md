# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Profile extraction improvements are complete for simple cases:
- `extract_simple_profiles` detects closed polygons from connected lines and circle entities
- Near-full arcs are treated as circles; arcs can be discretized
- Extrude uses polygon or circle profiles (faceted prism / cylinder) instead of only AABB
- Revolve uses extracted polygon for better radial/axial profile
- Research note: `docs/research/profile-extraction.md`

Next concrete work:

1. **Offset / symmetric improvements for Extrude**
   - Support start offset and symmetric extrude options in schema + feature + mesh generation
   - Research Fusion 360 / Onshape offset and two-direction extrude behavior

2. **Boolean operations (join/cut) on generated meshes**
   - Basic mesh boolean helpers or stubs for feature operations beyond "new"

3. Keep foundation solid; all existing tests must continue to pass.

After offset/symmetric, next increments:
- Rollback marker and feature reordering in the timeline
- Visual 2D canvas for sketching (mouse drawing, snapping)
- Better hole/nested profile support

## Recently Completed
- Better profile support: polygon + circle extraction, arc handling, improved Extrude/Revolve mesh generation
- Sketch editor editable cells (point coordinates, dimension values) + selection-aware entity addition
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
