# Extrude Operator Research

**Sources**: Blender Manual (docs.blender.org/manual/en/latest/modeling/meshes/editing/duplicating/extrude.html), Autodesk Maya Help, community tutorials (Artistic Render, Skillademia), comparison notes.

**Date**: 2026-11-14

## Core Concept

Extrude is the primary tool for adding new geometry connected to existing selection.

- **Vertices** → new vertices + edges
- **Edges** → new edges + faces
- **Faces** → new faces + side walls (the most common case)

The new geometry stays connected; the selection is “pulled out”.

## Blender Behavior (most relevant)

- Shortcut: **E** in Edit Mode.
- Default direction: averaged normal of selected faces (or free if no faces).
- Axis locking: press X/Y/Z (global) or XX/YY/ZZ (local/normal) while extruding.
- **Extrude Region** (default): selected faces move as a group; outer boundary edges become side faces.
- Internal edges (shared by ≥2 selected faces) are not turned into side walls.
- **Extrude Along Normals**: each face extruded along its own normal.
- **Extrude Individual**: each face extruded separately (like Keep Faces Together = off).
- **Extrude Manifold**: smart version that cleanly stitches intersections (similar to Maya Smart Extrude).
- Canceling (right-click after E) still creates the geometry but leaves it coplanar (useful for later scale/inset).

Important topological rule from Blender manual:
1. Determine the outer edge loop of the selection.
2. Turn those edges into side faces.
3. Duplicate the selected faces and connect them, or (for closed volumes) avoid internal faces.

## Maya Behavior

- Ctrl+E or Edit Mesh > Extrude.
- Keep Faces Together (default on): same as Blender region extrude.
- Off: individual face extrusions.
- Smart Extrude (newer): automatically repairs double faces and non-manifold results by stitching intersections (Boolean-like).

## Practical Implementation Priority for PyModeler

1. **Whole-mesh or selected-face region extrude** along average normal (or fixed axis) by a distance.  
   Creates new vertices for the extruded faces + side faces for the boundary.
2. Support “extrude then move” via existing transform or a dedicated command.
3. Later: per-face normals, individual faces, manifold/smart stitching.
4. Must be undoable via CommandStack.
5. Keep mesh schema-valid after operation (recompute edges if needed).

## Differences vs Related Tools

| Tool   | Effect                                      | Typical use          |
|--------|---------------------------------------------|----------------------|
| Extrude| Adds volume / new connected geometry        | Build form           |
| Inset  | Creates inner border on faces (no volume)   | Windows, panels      |
| Bevel  | Rounds/splits edges, adds intermediate faces| Soften hard edges    |

This research informs the first Extrude implementation: a simple region extrude on a list of face indices (or all faces) that duplicates the faces, creates side walls on the boundary, and translates the new faces by a vector.
