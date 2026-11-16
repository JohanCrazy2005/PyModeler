"""Basic mesh Boolean helpers (Join / Cut / Intersect).

Uses trimesh + optional manifold3d when available (robust, cross-platform).
Falls back to simple concatenation for Join; raises a clear error for Cut/Intersect
if no Boolean engine is present.
"""

from __future__ import annotations

from typing import Literal, Optional

from .mesh import Mesh

BooleanOp = Literal["join", "cut", "intersect"]


class BooleanError(RuntimeError):
    """Raised when a Boolean operation cannot be performed."""


def _to_trimesh(mesh: Mesh):
    """Convert our Mesh to a trimesh.Trimesh (triangulated)."""
    try:
        import trimesh
        import numpy as np
    except ImportError as e:
        raise BooleanError("trimesh is required for mesh Booleans") from e

    verts = np.asarray(mesh.vertices, dtype=float)
    faces = mesh.faces
    # Ensure all faces are triangles for the Boolean engine
    tris = []
    for f in faces:
        if len(f) == 3:
            tris.append(f)
        elif len(f) == 4:
            # Fan or simple split
            tris.append([f[0], f[1], f[2]])
            tris.append([f[0], f[2], f[3]])
        else:
            # Fan from first vertex
            for i in range(1, len(f) - 1):
                tris.append([f[0], f[i], f[i + 1]])
    if not tris:
        raise BooleanError("Mesh has no faces")
    return trimesh.Trimesh(vertices=verts, faces=np.asarray(tris, dtype=int), process=False)


def _from_trimesh(tm, name: str = "Boolean") -> Mesh:
    """Convert a trimesh result back to our Mesh."""
    verts = tm.vertices.tolist()
    faces = tm.faces.tolist()
    return Mesh(vertices=verts, faces=faces, name=name)


def mesh_boolean(target: Mesh, tool: Mesh, operation: BooleanOp, name: Optional[str] = None) -> Mesh:
    """Apply a Boolean operation between two meshes.

    Parameters
    ----------
    target, tool : Mesh
        Solid (preferably watertight) meshes.
    operation : "join" | "cut" | "intersect"
    name : optional result name

    Returns
    -------
    Mesh
        Result of the operation.
    """
    op = operation.lower()
    if op not in ("join", "cut", "intersect"):
        raise BooleanError(f"Unknown Boolean operation: {operation}")

    result_name = name or f"{target.name}_{op}"

    try:
        import trimesh
        # Prefer manifold engine when available
        engine = None
        try:
            import manifold3d  # noqa: F401
            engine = "manifold"
        except ImportError:
            engine = None

        if engine is None:
            # Try default (may raise)
            engine = None

        a = _to_trimesh(target)
        b = _to_trimesh(tool)

        if op == "join":
            result = trimesh.boolean.union([a, b], engine=engine)
        elif op == "cut":
            result = trimesh.boolean.difference([a, b], engine=engine)
        else:  # intersect
            result = trimesh.boolean.intersection([a, b], engine=engine)

        if result is None or len(result.faces) == 0:
            raise BooleanError(f"Boolean {op} produced empty result")
        return _from_trimesh(result, name=result_name)

    except Exception as exc:
        # Fallback only for join: simple concatenation
        if op == "join":
            return _concatenate(target, tool, name=result_name)
        raise BooleanError(
            f"Boolean {op} failed (engine may be missing or meshes non-manifold): {exc}"
        ) from exc


def _concatenate(a: Mesh, b: Mesh, name: str) -> Mesh:
    """Simple vertex/face concatenation (union approximation when no real Boolean engine)."""
    offset = len(a.vertices)
    verts = [list(v) for v in a.vertices] + [list(v) for v in b.vertices]
    faces = [list(f) for f in a.faces] + [[i + offset for i in f] for f in b.faces]
    return Mesh(vertices=verts, faces=faces, name=name)
