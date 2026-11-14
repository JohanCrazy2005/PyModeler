# Blender Core Features (Research Summary)

**Sources**: Blender 5.x Manual (docs.blender.org), community tutorials, release notes (Blender 5.3), and comparison articles.  
**Focus**: Mesh modeling, viewport, materials/UV, basic animation, modifiers.  
**Date**: 2026-11-14

## 1. Mesh Structure
- **Vertices**, **Edges**, **Faces** (triangles/quads preferred; n-gons supported).
- Topology concepts: edge loops, face loops, poles.
- Selection modes: Vertex / Edge / Face (shortcuts 1/2/3 in Edit Mode).

## 2. Primitives (Add → Mesh)
Common starting points:
- Cube
- Plane
- UV Sphere / Ico Sphere
- Cylinder
- Cone
- Circle / Grid
- (Newer) Quad Sphere (good for subdivision)

## 3. Essential Modeling Tools (Edit Mode)
These cover the majority of everyday modeling work:

| Tool              | Shortcut   | Primary use                          | Elements     |
|-------------------|------------|--------------------------------------|--------------|
| Extrude           | E          | Add volume / new geometry            | V / E / F    |
| Inset             | I          | Create inner border on faces         | Faces        |
| Loop Cut & Slide  | Ctrl+R     | Add edge loops while preserving flow | Edges        |
| Bevel             | Ctrl+B     | Round sharp edges/vertices           | V / E / F    |
| Knife             | K          | Freehand cut                         | —            |
| Merge / Dissolve  | M / X      | Clean topology                       | V / E / F    |
| Subdivide         | —          | Increase density                     | —            |
| Boolean (op)      | —          | Union / Difference / Intersect       | Objects      |

Additional useful operators: Bridge, Rip, Separate, Join, Shade Smooth/Flat.

## 4. Modifiers (Non-destructive stack)
Key Generate modifiers used constantly:
- **Subdivision Surface** (Catmull-Clark) – organic smoothness
- **Bevel** – procedural edge rounding
- **Mirror** – symmetry
- **Array** – repetition
- **Solidify** – thickness
- **Boolean** – CSG operations
- **Mirror**, **Displace**, **Decimate**, **Remesh**, etc.

Order matters; can be applied to bake into the mesh.

## 5. Viewport & Navigation
- Orbit: middle-mouse drag
- Pan: Shift + middle-mouse
- Zoom: scroll wheel
- Numpad views: 1 (front), 3 (right), 7 (top), 5 (persp/ortho)
- Shading modes: Solid, Wireframe, Material Preview, Rendered
- Grid + axes always visible
- Transform gizmos (translate/rotate/scale)

## 6. Materials & Shading
- Principled BSDF (PBR) is the default node.
- Parameters: Base Color, Metallic, Roughness, Specular, Normal, Emission, etc.
- Shader Editor (nodes).
- Material slots on objects.
- Viewport solid / material preview / rendered.

## 7. UV Mapping
- UV Editor workspace.
- Mark Seams → Unwrap (Smart UV Project, Cube Projection, etc.).
- UV islands, packing, pinning.
- Texture painting (basic).

## 8. Animation Basics
- Keyframes (I to insert).
- Timeline, Dope Sheet, Graph Editor.
- Transform keyframes (location/rotation/scale).
- Simple object animation; later armatures / shape keys.

## 9. Other Core Capabilities
- Outliner (scene hierarchy / collections)
- Properties panel (object, mesh, material, modifiers…)
- Import/Export: OBJ, glTF/GLB, FBX, STL, PLY, USD, etc.
- Python scripting API + add-ons
- Sculpt mode (separate workflow)
- Basic physics / particles (later)

## Implications for PyModeler
Priority order for early implementation should follow the tools that professional modelers use daily:
1. Solid data model (mesh + scene + transforms)
2. Primitives
3. Real viewport + camera + selection
4. Transform gizmos
5. Extrude / Inset / Loop Cut / Bevel
6. Modifiers (start with Mirror, Subsurf, Bevel)
7. Materials (simple PBR) + UV
8. I/O (OBJ + glTF)
9. Undo/Redo, selection modes, outliner
10. Basic animation keyframes

This matches and expands the existing Phase 1–4 checklist.
