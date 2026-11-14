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
1. **Polish Phase 2 Viewport** (basic widget is live):
   - Improve mesh rendering (wireframe toggle, better lighting / flat shading with normals).
   - Selection highlighting in the viewport (object mode) once Selection system lands.
   - Frame-selected / frame-all camera shortcuts.
2. **Selection system** (object mode first) – mark selected objects, highlight in outliner + viewport.
3. **Undo/Redo command stack** (command pattern) so add/delete/transform can be reversed.
4. Continue refining PLAN.md with more detailed Phase 2 steps.
5. Ensure CI remains green; add more platforms (macOS/Windows) later if needed.

## Recently Completed
- Phase 1 primitives (Cube, Plane, Sphere, Cylinder, Cone) complete.
- CI workflow (`.github/workflows/ci.yml`) using QT_QPA_PLATFORM=offscreen.
- First moderngl + QOpenGLWidget viewport: ground grid, RGB axes, scene meshes, orbit/pan/zoom camera.
- Viewport gracefully falls back when OpenGL is unavailable (headless CI).
- Tests for viewport creation, scene binding, camera math, and MainWindow integration.

## Notes for Automation
- Always re-read GOAL.md, CHECKLIST.md, PLAN.md, and this file at the start of a run.
- **First action on new phases or large tasks**: perform or extend the web research and document it.
- After implementing, update CHECKLIST (mark items), rewrite this NEXT_STEPS with the new immediate priorities, and keep PLAN accurate.
- Test locally in the sandbox before pushing.
- Prefer small, complete, tested increments.
- Put research outputs and any generated artifacts under `docs/research/` or `output/` as appropriate.
- Current research documents: `docs/research/blender-core-features.md`, `docs/research/feature-inventory.md`, `docs/research/viewport-essentials.md`.
