# PyModeler Feature Inventory (Prioritized)

Synthesized from research on Blender (primary), with cross-checks against Maya, 3ds Max, and Cinema 4D.

**Goal**: A professional modeler can create, edit, texture, UV, and export basic production assets without leaving PyModeler for core modeling tasks.

## Priority Tiers

### P0 – Foundation (must exist before anything else)
- [ ] Robust Mesh data model (vertices, faces, optional edges/normals/UVs) + JSON Schema
- [ ] Scene graph: objects, hierarchy, transforms (location/rotation/scale)
- [ ] JSON Schema for Scene / SceneObject
- [ ] Undo/Redo command stack
- [ ] Basic PyQt6 application shell (menus, outliner, properties, status)
- [ ] Cross-platform packaging & CI skeleton

### P1 – Core Modeling Experience (Phase 1–2)
- Primitives: Cube, Plane, Sphere (UV), Cylinder, Cone
- Real OpenGL/moderngl viewport
- Camera: orbit / pan / zoom + orthographic/perspective
- Grid + axes
- Object selection in viewport
- Transform gizmos (translate / rotate / scale)
- Selection modes: Object / Vertex / Edge / Face
- Basic mesh display (shaded + wireframe overlay)

### P2 – Essential Editing Tools (Phase 3)
- Extrude (vertices/edges/faces)
- Inset
- Loop Cut & Slide
- Bevel
- Merge / Dissolve / Delete
- Subdivide
- Simple Boolean (via trimesh or similar)
- Shade Smooth / Flat

### P3 – Materials, UV & I/O (Phase 4)
- Simple material system (PBR parameters) + schema
- Material slots
- Basic image textures
- UV editor + at least Smart UV Project / cube projection
- Import: OBJ, glTF
- Export: OBJ, glTF, STL

### P4 – Non-destructive & Productivity
- Modifier stack (start with: Mirror, Subdivision Surface, Bevel, Array, Solidify)
- Outliner improvements + collections
- Keyboard shortcuts matching common conventions where sensible
- Snapping (grid, vertex, edge, face)

### P5 – Animation & Advanced (Phase 5+)
- Keyframe system (location/rotation/scale)
- Timeline + Dope Sheet basics
- Python console / scripting API
- Plugin/add-on loader
- Later: sculpting basics, simple path tracing, armatures

## Comparison Notes
- **Blender**: Strong all-rounder; excellent free reference for mesh tools, modifiers, UV, and viewport UX.
- **Maya**: Industry standard for animation/rigging; deep construction history and constraints. Useful later for animation/rigging design.
- **3ds Max**: Excellent hard-surface modeling and modifier stack; strong in archviz. Modifier order and editable poly concepts are relevant.
- **Cinema 4D**: Fast interactive modeling and motion graphics (MoGraph). Good for UX ideas around speed and designer-friendly tools.

## Recommended Immediate Build Order (after this research)
1. Complete and test missing foundation modules (Scene, MainWindow, schemas, tests).
2. Add remaining primitives (Plane, Sphere, Cylinder, Cone).
3. Implement real viewport (moderngl or PyOpenGL) with camera + grid.
4. Object selection + transform gizmos.
5. First mesh tools: Extrude + Inset.
6. Simple material system.
7. OBJ import/export.

This inventory will be refined as more research is performed on specific areas (e.g., before starting UV or animation).
