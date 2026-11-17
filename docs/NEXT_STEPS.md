# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Light UI integration of Parts is complete.**

- MainWindow now holds `self.current_part` (and `self.parts` list).
- FeatureTree and PropertyPanel are wired to the current Part’s FeatureHistory and ParameterStore.
- Extrude of the current sketch adds the sketch + ExtrudeFeature to the Part and recomputes the body mesh into the scene.
- Manufacturing menu → “Show Cut List” generates and displays a text cut list for the current parts.

### Next concrete tasks (Phase 2)
1. Begin simple Assembly container (references to Parts + basic transforms; mates later). Schema + core data model first.
2. DXF export stub for 2D profiles using ezdxf (add dependency when ready).
3. Optional: group cut-list items by material / thickness; CSV export helper.
4. Multi-part switching UI (list of parts, switch current_part).

## Recently Completed
- Light UI integration: MainWindow works with Part (FeatureTree, recompute body, cut-list display)
- Cut list / part list generation stub (schema + generator + tests)
- Material / stock definitions (schema + MaterialStore + default library)
- Multi-feature Part model (sketches + parameters + FeatureHistory → body mesh)
- Research note: docs/research/part-model.md, docs/research/material-stock.md, docs/research/cutlist.md

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
