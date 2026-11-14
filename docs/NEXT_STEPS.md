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
1. **Web research phase (highest priority now)**:
   - Search for and summarize core features of Blender (especially modeling, mesh tools, viewport, materials, UV, animation basics).
   - Do the same for Maya, 3ds Max, Cinema 4D where useful.
   - Create `docs/research/` folder and write structured notes (e.g. `docs/research/blender-core-features.md`, `docs/research/feature-inventory.md`).
   - Produce a prioritized list of capabilities PyModeler should eventually have.
2. Based on the research, refine the step-by-step build plan in PLAN.md and update CHECKLIST.md with more concrete items.
3. Finish any remaining foundation code (ensure all core modules, tests, and schemas are complete and pushed).
4. Then continue with concrete next features according to the new plan:
   - More primitives (Plane, Sphere, Cylinder, Cone)
   - Improve outliner → properties panel
   - Real OpenGL / moderngl viewport + camera + grid

## Notes for Automation
- Always re-read GOAL.md, CHECKLIST.md, PLAN.md, and this file at the start of a run.
- **First action on new phases or large tasks**: perform or extend the web research and document it.
- After implementing, update CHECKLIST (mark items), rewrite this NEXT_STEPS with the new immediate priorities, and keep PLAN accurate.
- Test locally in the sandbox before pushing.
- Prefer small, complete, tested increments.
- Put research outputs and any generated artifacts under `docs/research/` or `output/` as appropriate.
