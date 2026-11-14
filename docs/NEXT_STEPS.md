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
1. **Finish Phase 1 primitives** (highest value now that foundation + research are done):
   - Implement `create_plane`, `create_sphere` (UV sphere), `create_cylinder`, `create_cone` in `src/pymodeler/core/mesh.py`.
   - Keep them schema-valid.
   - Add unit tests.
   - Expose them in the Add → Mesh menu of the main window.
2. Add a simple GitHub Actions CI workflow that runs the tests (offscreen Qt if needed).
3. Then start Phase 2: real viewport research note + first moderngl/PyOpenGL widget with camera and grid.
4. Continue with selection system and Undo/Redo.

## Notes for Automation
- Always re-read GOAL.md, CHECKLIST.md, PLAN.md, and this file at the start of a run.
- **First action on new phases or large tasks**: perform or extend the web research and document it.
- After implementing, update CHECKLIST (mark items), rewrite this NEXT_STEPS with the new immediate priorities, and keep PLAN accurate.
- Test locally in the sandbox before pushing.
- Prefer small, complete, tested increments.
- Put research outputs and any generated artifacts under `docs/research/` or `output/` as appropriate.
- Current research documents: `docs/research/blender-core-features.md` and `docs/research/feature-inventory.md`.
