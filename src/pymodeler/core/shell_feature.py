"""Parametric ShellFeature: hollow solid to constant wall thickness.

Supports inside / outside / both directions, optional face openings with rim walls,
mitered vertex-normal offset for near-constant thickness, and Boolean difference
when trimesh + manifold3d are available (falls back to wall-stitching otherwise).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import math

from .mesh import Mesh
from .parameters import ParameterStore
from .features_core import FeatureValidationError, validate_shell_data, _new_id, _resolve_value


class ShellFeature:
    """Hollow a solid mesh to a constant wall thickness, optionally removing faces as openings."""

    def __init__(
        self,
        thickness: float | str = 1.0,
        name: str = "Shell",
        faces: Optional[Sequence] = None,
        direction: str = "inside",
        operation: str = "modify",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("shell")
        self.type = "shell"
        self.name = name
        self.thickness = thickness
        self.faces = list(faces) if faces is not None else []
        self.direction = direction if direction in ("inside", "outside", "both") else "inside"
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "thickness": self.thickness,
            "faces": self.faces,
            "direction": self.direction,
            "operation": self.operation,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_shell_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ShellFeature":
        validate_shell_data(data)
        return cls(
            thickness=data["thickness"],
            name=data.get("name", "Shell"),
            faces=data.get("faces"),
            direction=data.get("direction", "inside"),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_thickness(self, parameters: Optional[ParameterStore] = None) -> float:
        t = _resolve_value(self.thickness, parameters, 1.0)
        if t <= 0:
            raise FeatureValidationError(f"Shell thickness must be positive, got {t}")
        return t

    def apply_to_mesh(self, mesh: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Return a new Mesh that is the shelled version of ``mesh``."""
        thickness = self.resolved_thickness(parameters)
        direction = self.direction

        # Prefer Boolean path when engine available and no openings (or openings handled after)
        try:
            from .boolean import mesh_boolean
            has_engine = True
        except Exception:
            has_engine = False

        if has_engine and not self.faces:
            try:
                result = self._boolean_shell(mesh, thickness, direction)
                if result is not None and len(result.faces) > 0:
                    return result
            except Exception:
                pass  # fall through to wall method

        # Wall-stitching path (always works; also used for openings)
        return self._wall_stitch_shell(mesh, thickness, direction)

    def _offset_mesh_inward(self, mesh: Mesh, thickness: float) -> Mesh:
        """Return a new Mesh whose vertices are offset inward by approximately ``thickness``."""
        return self._offset_mesh(mesh, -abs(thickness))

    def _offset_mesh_outward(self, mesh: Mesh, thickness: float) -> Mesh:
        return self._offset_mesh(mesh, abs(thickness))

    def _offset_mesh(self, mesh: Mesh, signed_thickness: float) -> Mesh:
        """Miter-corrected vertex-normal offset.

        scale_i = |t| / max(|vn · fn|) over adjacent faces (clamped).
        Vertices move along their (area-weighted) vertex normal.
        """
        try:
            import numpy as np
            from .boolean import _to_trimesh, repair_mesh
        except Exception:
            # Pure-Python fallback: simple centroid scale
            return self._centroid_scale_offset(mesh, signed_thickness)

        try:
            repaired = repair_mesh(mesh)
            tm = _to_trimesh(repaired)
            # Ensure normals
            if tm.vertex_normals is None or len(tm.vertex_normals) == 0:
                tm.fix_normals()
            vn = np.asarray(tm.vertex_normals, dtype=float)
            # Normalize
            norms = np.linalg.norm(vn, axis=1, keepdims=True)
            norms = np.where(norms < 1e-12, 1.0, norms)
            vn = vn / norms

            # Build per-vertex max |vn · face_normal| for miter correction
            face_normals = np.asarray(tm.face_normals, dtype=float)
            scales = np.full(len(tm.vertices), abs(signed_thickness), dtype=float)
            for fi, face in enumerate(tm.faces):
                fn = face_normals[fi]
                fn_n = np.linalg.norm(fn)
                if fn_n < 1e-12:
                    continue
                fn = fn / fn_n
                for vi in face:
                    dot = abs(float(np.dot(vn[vi], fn)))
                    if dot > 1e-6:
                        # miter scale so the offset distance along normal projects correctly
                        scales[vi] = max(scales[vi], abs(signed_thickness) / dot)
            # Clamp extreme miters
            scales = np.clip(scales, abs(signed_thickness), abs(signed_thickness) * 4.0)

            sign = 1.0 if signed_thickness > 0 else -1.0
            offset_verts = tm.vertices + sign * scales[:, None] * vn

            from .boolean import _from_trimesh
            return _from_trimesh(
                type(tm)(vertices=offset_verts, faces=tm.faces),
                name=f"{mesh.name}_offset",
            )
        except Exception:
            return self._centroid_scale_offset(mesh, signed_thickness)

    def _centroid_scale_offset(self, mesh: Mesh, signed_thickness: float) -> Mesh:
        """Fallback: scale about centroid (approximate, only good for convex near-origin)."""
        if not mesh.vertices:
            return mesh
        cx = sum(v[0] for v in mesh.vertices) / len(mesh.vertices)
        cy = sum(v[1] for v in mesh.vertices) / len(mesh.vertices)
        cz = sum(v[2] for v in mesh.vertices) / len(mesh.vertices)
        # Estimate scale factor from average distance
        dists = [math.hypot(v[0] - cx, v[1] - cy, v[2] - cz) for v in mesh.vertices]
        avg = sum(dists) / max(len(dists), 1) or 1.0
        factor = 1.0 + signed_thickness / avg
        new_verts = [
            [cx + (v[0] - cx) * factor, cy + (v[1] - cy) * factor, cz + (v[2] - cz) * factor]
            for v in mesh.vertices
        ]
        return Mesh(vertices=new_verts, faces=[list(f) for f in mesh.faces], name=f"{mesh.name}_scaled")

    def _boolean_shell(self, mesh: Mesh, thickness: float, direction: str) -> Optional[Mesh]:
        from .boolean import mesh_boolean

        if direction == "inside":
            inner = self._offset_mesh_inward(mesh, thickness)
            return mesh_boolean(mesh, inner, "cut", name=f"{mesh.name}_shell")
        elif direction == "outside":
            outer = self._offset_mesh_outward(mesh, thickness)
            return mesh_boolean(outer, mesh, "cut", name=f"{mesh.name}_shell")
        else:  # both
            half = thickness / 2.0
            outer = self._offset_mesh_outward(mesh, half)
            inner = self._offset_mesh_inward(mesh, half)
            return mesh_boolean(outer, inner, "cut", name=f"{mesh.name}_shell")

    def _wall_stitch_shell(self, mesh: Mesh, thickness: float, direction: str) -> Mesh:
        """Build shell by offsetting and connecting walls; add rim walls for openings."""
        if direction == "outside":
            outer = self._offset_mesh_outward(mesh, thickness)
            inner = mesh
        elif direction == "both":
            half = thickness / 2.0
            outer = self._offset_mesh_outward(mesh, half)
            inner = self._offset_mesh_inward(mesh, half)
        else:  # inside
            outer = mesh
            inner = self._offset_mesh_inward(mesh, thickness)

        # Map named faces ("top", "bottom", ...) to indices for the cube-like case
        opening_indices = self._resolve_opening_indices(outer)

        # Collect all outer faces except openings, all inner faces (flipped), and walls
        verts: List[List[float]] = [list(v) for v in outer.vertices] + [list(v) for v in inner.vertices]
        n_outer = len(outer.vertices)
        faces: List[List[int]] = []

        # Outer faces (skip openings)
        for i, f in enumerate(outer.faces):
            if i not in opening_indices:
                faces.append(list(f))

        # Inner faces (reverse winding so normals point into the cavity)
        for f in inner.faces:
            faces.append([vi + n_outer for vi in reversed(f)])

        # Connecting walls between corresponding outer/inner faces that are not openings
        # For every non-opening outer face, create side walls along its edges to the matching inner face
        for i, oface in enumerate(outer.faces):
            if i in opening_indices:
                continue
            iface = inner.faces[i] if i < len(inner.faces) else None
            if iface is None or len(iface) != len(oface):
                continue
            # For each edge of the face, make a quad wall
            m = len(oface)
            for k in range(m):
                o0 = oface[k]
                o1 = oface[(k + 1) % m]
                i0 = iface[k] + n_outer
                i1 = iface[(k + 1) % m] + n_outer
                # Wall quad (outward-ish)
                faces.append([o0, o1, i1, i0])

        # Rim walls for openings: connect outer boundary of removed face to inner boundary
        for oi in opening_indices:
            if oi >= len(outer.faces) or oi >= len(inner.faces):
                continue
            oface = outer.faces[oi]
            iface = inner.faces[oi]
            if len(oface) != len(iface):
                continue
            m = len(oface)
            for k in range(m):
                o0 = oface[k]
                o1 = oface[(k + 1) % m]
                i0 = iface[k] + n_outer
                i1 = iface[(k + 1) % m] + n_outer
                # Rim wall (points inward)
                faces.append([o0, o1, i1, i0])

        return Mesh(vertices=verts, faces=faces, name=f"{mesh.name}_shell")

    def _resolve_opening_indices(self, mesh: Mesh) -> set:
        """Convert self.faces (indices or names like 'top') into a set of face indices."""
        indices = set()
        if not self.faces:
            return indices
        # Simple name map for axis-aligned boxes (by dominant normal / position)
        name_to_idx = self._guess_named_faces(mesh)
        for f in self.faces:
            if isinstance(f, int):
                if 0 <= f < len(mesh.faces):
                    indices.add(f)
            elif isinstance(f, str):
                key = f.lower().strip()
                if key in name_to_idx:
                    indices.add(name_to_idx[key])
                elif key.isdigit():
                    idx = int(key)
                    if 0 <= idx < len(mesh.faces):
                        indices.add(idx)
        return indices

    def _guess_named_faces(self, mesh: Mesh) -> Dict[str, int]:
        """Best-effort mapping of 'top'/'bottom'/etc. for axis-aligned meshes."""
        result: Dict[str, int] = {}
        if not mesh.faces or not mesh.vertices:
            return result
        # Compute face centroids and approximate normals via Newell or cross of first edges
        centroids = []
        normals = []
        for f in mesh.faces:
            if len(f) < 3:
                centroids.append((0, 0, 0))
                normals.append((0, 0, 0))
                continue
            pts = [mesh.vertices[i] for i in f]
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            cz = sum(p[2] for p in pts) / len(pts)
            centroids.append((cx, cy, cz))
            # Simple normal from first triangle
            a, b, c = pts[0], pts[1], pts[2]
            nx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
            ny = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])
            nz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            nlen = math.hypot(nx, ny, nz) or 1.0
            normals.append((nx / nlen, ny / nlen, nz / nlen))

        # Find extremes
        if not centroids:
            return result
        zs = [c[2] for c in centroids]
        ys = [c[1] for c in centroids]
        xs = [c[0] for c in centroids]
        result["top"] = max(range(len(centroids)), key=lambda i: zs[i])
        result["bottom"] = min(range(len(centroids)), key=lambda i: zs[i])
        result["back"] = max(range(len(centroids)), key=lambda i: ys[i])
        result["front"] = min(range(len(centroids)), key=lambda i: ys[i])
        result["right"] = max(range(len(centroids)), key=lambda i: xs[i])
        result["left"] = min(range(len(centroids)), key=lambda i: xs[i])
        return result
