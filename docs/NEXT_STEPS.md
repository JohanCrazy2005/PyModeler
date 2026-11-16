# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Visual 2D sketch canvas is now available:
- QGraphicsView-based canvas inside the Sketch Editor dialog
- Mouse drawing for Point / Line / Circle modes
- Basic point snapping
- Live preview while dragging
- Bidirectional sync with the Sketch data model and table views

Next concrete work:

1. **Wire recompute into the main window / viewport**
   - When features or rollback change, regenerate meshes and display them in the viewport
   - Connect FeatureHistory.recompute_meshes to scene objects

2. **Improve canvas interaction**
   - Better selection of entities on the canvas
   - Drag existing points to update coordinates
   - Arc tool, rectangle tool on canvas
   - Constraint badges / visual feedback

3. Keep foundation solid; all existing tests must continue to pass.

After viewport wiring:
- Multi-feature Part model
- Dependency-aware reordering (parent/child checks)
- Better hole/nested profile support

## Recently Completed
- Visual 2D sketch canvas (QGraphicsView) with point/line/circle drawing and snapping
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
