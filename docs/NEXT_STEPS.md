# Next Steps (Living Document)

This file is updated by every automation run. It should always contain the concrete, ordered actions for the immediate future.

## Critical Process Instruction (for every automation run)
**Before starting significant new feature work:**
1. Look on the web for comprehensive feature lists and documentation of top modeling software (Blender, Maya, 3ds Max, Cinema 4D, Houdini, etc.).
2. Document the findings (create or update files under `docs/research/` or expand GOAL.md / PLAN.md).
3. Only after research is done: plan the step-by-step implementation of the prioritized features.
4. Then implement, test, and update the living docs.

This research-first → plan → build cycle must be followed for every new major area.

## Immediate Priority (Next runs)
1. **Improve Phase 2 Viewport**:
   - Add solid/filled shading option (toggle wireframe/solid).
   - Apply full transform (rotation + scale) in the viewport drawing.
   - Highlight selected object(s) differently.
2. **Selection system** (object mode first):
   - Research note if needed, then implement outliner + viewport click selection.
   - Store selection on Scene or MainWindow.
3. **Undo/Redo command stack** (Phase 1 remaining).
4. Ensure CI remains green; consider software OpenGL fallback if needed.

## Notes for Automation
- Always re-read GOAL.md, CHECKLIST.md, PLAN.md, and this file at the start of a run.
- **First action on new phases or large tasks**: perform or extend the web research and document it.
- After implementing, update CHECKLIST (mark items), rewrite this NEXT_STEPS with the new immediate priorities, and keep PLAN accurate.
- Test locally in the sandbox before pushing.
- Prefer small, complete, tested increments.
- Put research outputs and any generated artifacts under `docs/research/` or `output/` as appropriate.
- Current research documents: `docs/research/blender-core-features.md`, `docs/research/feature-inventory.md`, `docs/research/viewport-essentials.md`.
- Phase 1 primitives complete. Basic viewport (grid, axes, wireframe meshes, orbit/pan/zoom) is implemented using PyOpenGL + QOpenGLWidget.
