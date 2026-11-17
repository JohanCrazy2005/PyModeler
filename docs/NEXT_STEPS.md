# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Cut-list enhancements complete.**

- `group_cut_list()` groups items by material, thickness, or material+thickness (Mozaik-style).
- Thickness is taken from material.thickness when present, otherwise the minimum bounding-box dimension.
- `cut_list_to_csv()` exports a clean CSV (optional group column).
- `cut_list_to_grouped_text()` and `CutList` methods (`groups()`, `to_csv()`, `to_grouped_text()`).
- Existing `generate_cut_list` / schema unchanged and fully backward-compatible.
- Tests cover grouping, CSV, and class helpers.

### Next concrete tasks (Phase 2)
1. Assembly mates schema + basic rigid/fastened mate solver.
2. Viewport polish / selection improvements.
3. Basic BOM generation.
4. Optional: UI exposure of grouped cut-list / CSV export button.

## Recently Completed
- Cut-list enhancements: grouping by material/thickness + CSV export helper
- Multi-part switching UI (parts list + switch + feature tree update)
- DXF export stub for 2D sketches and closed profiles (ezdxf)
- Simple Assembly container (schema + core data model + tests + research note)
- Light UI integration: MainWindow works with Part (FeatureTree, recompute body, cut-list display)
- Cut list / part list generation stub (schema + generator + tests)
- Material / stock definitions (schema + MaterialStore + default library)
- Multi-feature Part model (sketches + parameters + FeatureHistory → body mesh)

## Notes for Automation
- The end goal is a tool that feels like Fusion 360 / Onshape for parametric design and has practical manufacturing helpers like Mozaik (cut lists, nesting concepts, etc.).
- Always prefer parametric, history-based, dimension-driven modeling over pure mesh editing.
- **ezdxf is approved and preferred** for any DXF read/write, 2D drawing export, and manufacturing-related DXF workflows. Use it from `src/pymodeler/io/` when implementing DXF support.
- Keep main branch runnable and tested. Small complete increments.
