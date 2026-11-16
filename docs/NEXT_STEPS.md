# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

Constraint visual feedback completed:
- Colored circular badges near constrained entities on the sketch canvas
- Short type labels (HOR, VER, EQU, …)
- Hover tooltips showing constraint type, entities, and ID
- Research note in docs/research/constraint-visual-feedback.md

Next concrete work:

1. **Fully constrained sketch validation (DOF analysis stub)**
   - Simple degrees-of-freedom counting or status flags on entities
   - Color entities blue (under) / black (fully) as in Fusion/Onshape
   - Schema extension if needed for status

2. **Multi-feature Part model**
   - Schema + data model for a Part that owns sketches + FeatureHistory
   - Dependency-aware reordering (parent/child checks)

3. Keep foundation solid; all existing tests must continue to pass.

After canvas polish:
- Better hole/nested profile support
- DXF export stubs using **ezdxf** (now an approved library)

## Recently Completed
- Constraint visual feedback / badges on sketch canvas (markers + tooltips)
- Improved canvas: select mode, point dragging, rectangle tool with basic constraints, arc tool stub
- Added Sketch.update_point helper
- Wired FeatureHistory.recompute_meshes into MainWindow so feature/rollback changes update the viewport
- Restored full ExtrudeFeature / RevolveFeature / FeatureHistory implementation (features.py was a placeholder)
- Documented **ezdxf** as an approved dependency for DXF I/O and dimensioned/manufacturing drawing outputs
- Visual 2D sketch canvas (QGraphicsView) with point/line/circle drawing and snapping
- Feature tree context menu to set rollback marker + visual [suppressed] indication
- UI: Property panel now edits Extrude start_offset (and distance/angle)
- Rollback marker + basic feature reordering (data model, schema, recompute, tests)
- Basic mesh Boolean helpers (join/cut/intersect) + FeatureHistory integration
- Extrude start offset + symmetric refinements
- Better profile support: polygon + circle extraction, arc handling
- Sketch editor editable cells + selection-aware entity addition
- Revolve feature (schema, parameter-driven angle, faceted solid of revolution)
- Basic 2D sketch editor widgets (table-based)
- Feature tree / timeline UI stub + property panel
- ExtrudeFeature + FeatureHistory
- Research notes for parametric Extrude
- ParameterStore + JSON Schema + expression evaluation
- Sketch JSON Schema + core data model

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- Keep JSON schemas as the source of truth for all data.
- Test before every push. Keep main runnable.
- Put research outputs in `docs/research/` and any generated examples in `output/`.
- Research documents for Fusion, Onshape, and Mozaik are in place; consult them before expanding Phase 1.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
