# Inset Operator Research

**Sources**: Blender Manual (docs.blender.org/manual/en/latest/modeling/meshes/editing/face/inset_faces.html), Artistic Render, Cinema 4D Extrude Inner / Inset docs, community notes.

**Date**: 2026-11-14

## Core Concept

Inset creates a border of new faces around the selected faces by scaling the selection inward (or outward for outset). The original outer boundary stays in place; a new inner face (or faces) is created, connected by side quads.

Typical uses: windows, panels, bevel preparation, surface detail without adding volume (unless depth is applied).

Unlike Extrude (which adds volume along a normal), pure Inset keeps the mesh roughly planar to the original faces.

## Blender Behavior (most relevant)

- Shortcut: **I** in Edit Mode (Face mode preferred).
- Modal: drag to set Thickness; hold Ctrl to also set Depth.
- **Region (default)**: selected faces treated as connected patches; only the outer boundary of each patch is inset. Internal edges stay shared.
- **Individual**: each selected face is inset independently (toggle with I again while active).
- Options:
  - Thickness: absolute size of the border.
  - Depth: raise/lower the inner faces along normals.
  - Boundary: whether open boundary edges produce border faces.
  - Offset Even / Offset Relative: control evenness of the border width.
  - Edge Rail: align new edges to existing rails.
  - Outset: grow outward instead of inward.
  - Select Outer: after operation, select the border faces instead of the inner ones.
- Multiple disjoint patches can be processed in one call.

## Cinema 4D

- Formerly “Extrude Inner”.
- Similar interactive drag for offset.
- Options include Preserve Groups (region vs individual), Offset Variation, Subdivision.

## Practical Implementation Priority for PyModeler

1. **Individual face inset** (simplest, robust): for each selected face, create new vertices moved toward the face centroid by a thickness fraction, replace the face with the inset face, and add border quads for every edge.
2. Optional Depth: translate the new inset vertices along the face normal.
3. Undoable via CommandStack (snapshot mesh).
4. Later: true region inset (shared vertices on internal edges, only outer boundary), absolute thickness, Offset Even, outset, edit-mode selection.
5. Keep mesh schema-valid; clear derived edges/normals so they can be recomputed.

## Basic Algorithm (Individual)

For each face:
- Compute centroid C.
- For each vertex Vi, new_Vi = Vi + thickness * (C - Vi)   (thickness in [0, 1]).
- Optionally add depth * normal to new_Vi.
- Emit border quad per original edge: [orig_a, orig_b, new_b, new_a].
- Replace original face with the new inset face (same winding).

This produces one new inner face + N border faces per original N-gon and is fully schema-valid.

## Differences vs Related Tools

| Tool   | Effect                                      | Typical use          |
|--------|---------------------------------------------|----------------------|
| Extrude| Adds volume / new connected geometry        | Build form           |
| Inset  | Creates inner border on faces (planar)      | Windows, panels      |
| Bevel  | Rounds/splits edges, adds intermediate faces| Soften hard edges    |

This research informs the first Inset implementation: individual-face inset with thickness fraction and optional depth, exposed via Mesh.inset_faces + InsetMeshCommand, and a simple Mesh-menu entry.
