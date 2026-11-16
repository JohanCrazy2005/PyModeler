# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Rollback marker can now be set from the feature tree UI via right-click context menu ("Roll to here" / "Roll to end"). Features after the marker are visually marked [suppressed] and grayed. FeatureHistory + Extrude/Revolve data models are fully restored and tested. Property panel supports Extrude distance and start_offset.

Next concrete work:

1. **Visual 2D canvas for sketching**
   - Mouse drawing, basic snapping, preview of entities (research already exists in docs/research/sketch-editor-ui.md)

2. **Wire recompute into the main window / viewport**
   - When features or rollback change, regenerate meshes and display them in the viewport

3. Keep foundation solid; all existing tests must continue to pass.

After timeline UI improvements, next increments:
- Better hole/nested profile support
- Multi-feature Part model
- Dependency-aware reordering (parent/child checks)

## Recently Completed
- Feature tree context menu to set rollback marker + visual [suppressed] indication
- Restored full FeatureHistory + Extrude/Revolve implementations (rollback_marker, set_rollback, reorder, recompute_meshes suppression, offset/symmetric/operation)
- UI: Property panel now edits Extrude start_offset (and distance/angle)
- Rollback marker + basic feature reordering (data model, schema, recompute, tests)
- Basic mesh Boolean helpers (join/cut/intersect) + FeatureHistory integration
- Extrude start offset + symmetric refinements (schema, resolution, mesh generation)
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
