# Next Steps (Living Document)

This file is updated by every automation run. It should always contain the concrete, ordered actions for the immediate future.

## Immediate Priority (Next 1-3 runs)
1. Create and validate JSON Schema for Mesh (vertices, faces, normals, UVs).  ✅ Done
2. Implement a pure-Python Mesh class that validates against the schema.  ✅ Done
3. Implement Scene + SceneObject with transform (location, rotation, scale).  ✅ Done
4. Build a minimal PyQt6 MainWindow that shows:
   - Menu bar (File, Edit, Add)
   - Empty 3D viewport placeholder (QLabel or QOpenGLWidget stub)
   - Simple Outliner / Object list
   - Status bar
   ✅ Done
5. Add "Add → Mesh → Cube" that creates a schema-validated cube and adds it to the scene.  ✅ Done
6. Write pytest tests that:
   - Schema validation passes for valid cube
   - Schema rejects invalid data
   - Mesh class can be serialized/deserialized
   ✅ Done
7. Create requirements.txt and a simple run script.  ✅ Done
8. Push everything under the repository (code lives primarily under `src/` and planning under `docs/`; user requested an `output/` folder – we will also mirror key build artifacts there).

## Next After This Push
- Add more primitives (Plane, Sphere, Cylinder)
- Improve outliner selection → properties panel update
- Introduce a basic OpenGL / moderngl viewport widget
- Camera orbit / pan / zoom
- Simple grid

## Notes for Automation
- Always re-read GOAL.md, CHECKLIST.md, PLAN.md, and this file at the start of a run.
- After implementing, update CHECKLIST (mark items), update this NEXT_STEPS, and add a short entry to a CHANGELOG if useful.
- Test locally in the sandbox before pushing.
- Prefer small, complete, tested increments.
