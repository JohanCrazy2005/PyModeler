# Next Steps (Living Document)

This file is updated by every automation run.

## Critical Process (every run)
1. Read GOAL.md, CHECKLIST.md, PLAN.md, and this file.
2. **Research first** when entering a new area: look on the web at how Fusion 360, Onshape, and Mozaik implement the relevant features. Document findings in `docs/research/`.
3. Only after research: plan the concrete next implementation steps.
4. Implement small, tested increments. Update schemas, tests, and living docs. Push.

## Immediate Priority

**Assembly rigid/fastened mates complete.**

- Schema extended with optional `mates` array (type rigid|fastened, instance ids, offset transform).
- `Mate` class + `Assembly.add_mate` / `remove_mate` / `solve_mates`.
- Basic solver: if one instance is grounded, moves the other by the stored location offset.
- Fully backward-compatible; existing assemblies without mates still validate.
- Tests cover schema, round-trip, and solve behavior.
- Research note: `docs/research/assembly-mates.md`.

### Next concrete tasks (Phase 2)
1. Viewport polish / selection improvements.
2. Basic BOM generation.
3. Optional: UI exposure of mates + grouped cut-list / CSV export.
4. Optional: richer mate solver (rotation composition, revolute/slider stubs).

## Recently Completed
- Assembly mates: rigid/fastened schema + basic location-offset solver
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
