# Viewport Essentials Research Note

**Date**: 2026-11-14  
**Sources**: Blender Manual (Navigation), community guides, Maya Help (Tumble/Track/Dolly)

## Core Navigation (Must-have for Phase 2 first viewport)

### Blender (primary reference)
- **Orbit**: Middle mouse button drag (rotate around point of interest / selection).
- **Pan**: Shift + Middle mouse button drag.
- **Zoom**: Mouse wheel or Ctrl + Middle mouse drag.
- **Frame selection**: Numpad . (period) or Home to fit all.
- **Standard views**: Numpad 1 (front), 3 (right), 7 (top); Ctrl variants for opposite.
- **Perspective / Orthographic**: Numpad 5 toggle.
- **Navigation gizmo**: Axis widget top-right; click axes to align, drag to orbit.
- **Grid**: Infinite grid on XZ (or configurable), axes displayed (X red, Y green, Z blue).
- **Selection highlighting**: Selected objects/meshes outlined or shaded differently.

### Maya
- **Tumble (orbit)**: Alt + left mouse drag.
- **Track (pan)**: Alt + middle mouse drag.
- **Dolly (zoom)**: Alt + right mouse drag.
- **Frame**: F (selected), A (all).
- Similar grid and axis conventions.

## Minimal Implementation Target for First Viewport Widget
1. PyQt6 widget hosting moderngl or PyOpenGL context.
2. Draw infinite grid (or large finite) on the ground plane.
3. Draw RGB axes at origin.
4. Draw all (or selected) scene meshes as simple wireframe or flat-shaded triangles.
5. Basic orbit camera:
   - Mouse left-drag or middle-drag → orbit (azimuth/elevation).
   - Shift + drag → pan.
   - Wheel → zoom (dolly).
6. Update on scene changes (object added, transform).
7. No selection yet (next step after basic drawing works).

## Later Viewport Features (deferred)
- Selection (raycast / GPU picking).
- Transform gizmos.
- Shading modes (wire, solid, material preview).
- Overlays (normals, edges, face dots).
- Multiple viewports / quad view.
- Camera view vs user view.

This note grounds the Phase 2 first increment. Implementation should start with a simple moderngl QOpenGLWidget subclass that renders the grid + meshes from the Scene.
