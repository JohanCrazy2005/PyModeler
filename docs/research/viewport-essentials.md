# Viewport Essentials Research Note

**Date**: 2026-11-14 (updated 2026-11-18)  
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

## Implemented (2026-11-18 polish)
- moderngl QOpenGLWidget with orbit/pan/zoom.
- Ground grid + properly colored RGB world axes.
- Flat-shaded meshes, wireframe, solid+edges modes.
- Standard views (front/right/top/etc.) and orthographic toggle.
- Keyboard: F/. frame selected, A/Home frame all, 1/3/7 views, 5 ortho, G/R/S gizmo.
- Click-to-select via AABB raycast; empty click clears selection.
- Transform gizmos (translate/rotate/scale) with local axes.

## Later Viewport Features (deferred)
- Selection outline / feature highlighting.
- Better gizmo arrowheads / rotation rings.
- Multiple viewports / quad view.
- Camera view vs user view.

This note grounds the Phase 3 viewport polish. Further interaction improvements can build on the current camera and selection foundation.
