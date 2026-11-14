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
1. Add a simple distance / axis-locking dialog or modal for Extrude (currently fixed at 1.0).
2. Improve side-face winding further and add visual normal overlay in the viewport.
3. Begin Inset operator research and basic implementation (docs/research/inset-operator.md).
4. Add overlay toggles (normals, edge highlighting).
5. Continue refining PLAN.md with more detailed Phase 3 steps.

## Recently Completed
- Improved Extrude: individual mode (each face extruded separately with its own sides), optional per-face normals, cleaner side-face winding. UI: Extrude Region (E) and Extrude Individual (Shift+E). ExtrudeMeshCommand updated; tests added.
- Wired Extrude into the UI: Mesh menu item + keyboard E (object mode: extrudes all faces of selected objects along the average face normal by distance 1.0). Uses existing ExtrudeMeshCommand for undo/redo. Updated keyboard shortcuts docs and tests.
- Basic Extrude operator: Mesh.extrude_faces (region extrude of selected face indices or whole mesh along a direction), ExtrudeMeshCommand for undo/redo, research document docs/research/extrude-operator.md, unit tests.
- Transform gizmos now respect object rotation (oriented local axes). Drag applies movement along the local axis using screen-space projection. Visual feedback: active axis drawn thicker and brighter during drag.
- Restored functional MainWindow (was placeholder): menus for Add/Edit/View/Gizmo/Help, outliner sync, undo/redo integration via CommandStack, Help → Keyboard Shortcuts dialog.
- Shading modes: solid, wireframe, solid+edges (edge overlay). Menu + Z toggle. Orthographic projection toggle (key 5). Standard views (front/right/top etc., keys 1/3/7).
- Full object transform (rotation + scale) now applied consistently in Frame All/Selected and click-to-select raycast AABB.
- Transform gizmos (translate / rotate / scale) for the primary selected object: axis-colored lines, click-drag to constrain, live preview, commit to Undo/Redo via SetTransformCommand. Keyboard G/R/S to switch modes. Full model matrix applied in mesh drawing.
- Phase 2 viewport polish: wireframe toggle (edge lines), flat shading with computed normals + simple lighting, Frame All / Frame Selected (Home/F), click-to-select via AABB raycast with outliner sync.
- Undo/Redo command stack (Command pattern) supporting AddObject, RemoveObject, and SetTransform.
- Integrated into MainWindow: Add primitives and Delete Selected use the history; Undo/Redo menu + Ctrl+Z / Ctrl+Shift+Z.
- Object-mode selection system on Scene (select / deselect / clear, by name or object).
- Outliner selection syncs to scene selection; newly added primitives are auto-selected.
- Selected objects highlighted with a distinct color in the moderngl viewport.
- Tests covering selection logic and history commands.
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
- Current research documents: `docs/research/blender-core-features.md`, `docs/research/feature-inventory.md`, `docs/research/viewport-essentials.md`, `docs/research/extrude-operator.md`.
