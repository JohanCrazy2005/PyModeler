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
1. **Start Phase 2 – Viewport** (research note written):
   - Research note exists: `docs/research/viewport-essentials.md`.
   - Then implement a first moderngl or PyOpenGL widget inside the PyQt6 main window that draws a grid and the currently selected mesh (or all scene meshes) with a basic orbit camera.
2. After the basic viewport is solid: Selection system (object mode first) and Undo/Redo command stack.
3. Continue refining PLAN.md with more detailed Phase 2 steps once the research note exists.
4. Ensure CI remains green; add more platforms (macOS/Windows) later if needed.

## Notes for Automation
- Always re-read GOAL.md, CHECKLIST.md, PLAN.md, and this file at the start of a run.
- **First action on new phases or large tasks**: perform or extend the web research and document it.
- After implementing, update CHECKLIST (mark items), rewrite this NEXT_STEPS with the new immediate priorities, and keep PLAN accurate.
- Test locally in the sandbox before pushing.
- Prefer small, complete, tested increments.
- Put research outputs and any generated artifacts under `docs/research/` or `output/` as appropriate.
- Current research documents: `docs/research/blender-core-features.md` and `docs/research/feature-inventory.md`.
- Phase 1 primitives (Cube, Plane, Sphere, Cylinder, Cone) are complete. CI workflow is in place (`.github/workflows/ci.yml`) using QT_QPA_PLATFORM=offscreen.
