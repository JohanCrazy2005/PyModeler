"""ShellFeature: constant-thickness shell via mitered offset + Boolean."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .mesh import Mesh
from .parameters import ParameterStore
from .features_core import FeatureValidationError, validate_shell_data, _new_id, _resolve_value


class ShellFeature:
    """Parametric shell with mitered Boolean offset (inside) and wall-stitch fallback."""

    def __init__(self, thickness: float | str = 1.0, name: str = "Shell", faces=None, direction: str = "inside", operation: str = "modify", metadata=None, id=None):
        self.id = id or _new_id("shell")
        self.type = "shell"
        self.name = name
        self.thickness = thickness
        self.faces = faces or []
        self.direction = direction if direction in ("inside", "outside", "both") else "inside"
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {"id": self.id, "type": self.type, "name": self.name, "thickness": self.thickness, "faces": self.faces, "direction": self.direction, "operation": self.operation}
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_shell_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ShellFeature":
        validate_shell_data(data)
        return cls(thickness=data["thickness"], name=data.get("name", "Shell"), faces=data.get("faces"), direction=data.get("direction", "inside"), operation=data.get("operation", "modify"), metadata=data.get("metadata"), id=data.get("id"))

    def resolved_thickness(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.thickness, parameters, 1.0)

    def apply_to_mesh(self, mesh: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        thickness = self.resolved_thickness(parameters)
        if thickness <= 0:
            raise FeatureValidationError("Shell thickness must be positive")
        if not self.faces and self.direction == "inside":
            try:
                result = self._boolean_shell(mesh, thickness)
                if result is not None and result.faces:
                    return result
            except Exception:
                pass
        return self._wall_stitch_shell(mesh, thickness)

    def _boolean_shell(self, mesh: Mesh, thickness: float) -> Optional[Mesh]:
        try:
            from .boolean import mesh_boolean
        except Exception:
            return None
        inner = self._offset_mesh_inward(mesh, thickness)
        if inner is None or not inner.faces:
            return None
        try:
            return mesh_boolean(mesh, inner, "cut", name=f"{mesh.name}_shell")
        except Exception:
            return None

    def _offset_mesh_inward(self, mesh: Mesh, thickness: float) -> Optional[Mesh]:
        try:
            import numpy as np
        except ImportError:
            return None
        verts = np.asarray(mesh.vertices, dtype=float)
        if len(verts) < 4 or not mesh.faces:
            return None
        new_verts = self._mitered_offset_vertices(verts, mesh.faces, thickness, inward=True)
        if new_verts is None:
            return None
        return Mesh(vertices=new_verts.tolist(), faces=[list(f) for f in mesh.faces], name=f"{mesh.name}_inner")

    def _mitered_offset_vertices(self, verts, faces: List[List[int]], thickness: float, inward: bool = True):
        try:
            import numpy as np
        except ImportError:
            return None
        n_verts = len(verts)
        face_normals = []
        for f in faces:
            if len(f) < 3:
                face_normals.append(np.zeros(3))
                continue
            v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
            n = np.cross(v1 - v0, v2 - v0)
            norm = np.linalg.norm(n)
            face_normals.append(n / norm if norm > 1e-12 else np.zeros(3))
        face_normals = np.asarray(face_normals)
        vert_face_idxs: List[List[int]] = [[] for _ in range(n_verts)]
        for fi, f in enumerate(faces):
            for vi in f:
                if 0 <= vi < n_verts:
                    vert_face_idxs[vi].append(fi)
        new_verts = verts.copy()
        sign = -1.0 if inward else 1.0
        eps = 0.1
        for vi in range(n_verts):
            idxs = vert_face_idxs[vi]
            if not idxs:
                continue
            adj_ns = face_normals[idxs]
            avg_n = adj_ns.mean(axis=0)
            anorm = np.linalg.norm(avg_n)
            if anorm < 1e-8:
                continue
            avg_n /= anorm
            scales = []
            for fn in adj_ns:
                cos_theta = float(np.dot(avg_n, fn))
                if cos_theta > eps:
                    scales.append(1.0 / cos_theta)
            miter = min(max(scales) if scales else 1.0, 4.0)
            new_verts[vi] = verts[vi] + sign * thickness * miter * avg_n
        return new_verts

    def _wall_stitch_shell(self, mesh: Mesh, thickness: float) -> Mesh:
        try:
            import numpy as np
        except ImportError:
            return mesh
        verts = np.asarray(mesh.vertices, dtype=float)
        faces = [list(f) for f in mesh.faces]
        if not faces or len(verts) == 0:
            return mesh
        open_indices = self._resolve_face_indices(faces, verts)
        sign = -1.0 if self.direction == "inside" else 1.0
        offset_thickness = thickness / 2.0 if self.direction == "both" else thickness
        if self.direction == "both":
            sign = -1.0
        inner_arr = self._mitered_offset_vertices(verts, faces, offset_thickness, inward=(sign < 0))
        if inner_arr is None:
            normals = []
            for f in faces:
                if len(f) < 3:
                    normals.append(np.zeros(3))
                    continue
                v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
                n = np.cross(v1 - v0, v2 - v0)
                norm = np.linalg.norm(n)
                normals.append(n / norm if norm > 1e-12 else np.zeros(3))
            normals = np.asarray(normals)
            v_normals = np.zeros_like(verts)
            for i, f in enumerate(faces):
                for vi in f:
                    if 0 <= vi < len(verts):
                        v_normals[vi] += normals[i]
            v_norms = np.linalg.norm(v_normals, axis=1, keepdims=True)
            v_norms[v_norms < 1e-12] = 1.0
            v_normals /= v_norms
            inner_verts = verts + sign * offset_thickness * v_normals
        else:
            inner_verts = inner_arr
        result_verts = verts.tolist() + inner_verts.tolist()
        n_outer = len(verts)
        result_faces: List[List[int]] = []
        for i, f in enumerate(faces):
            if i not in open_indices:
                result_faces.append(f)
        for i, f in enumerate(faces):
            if i not in open_indices:
                result_faces.append([n_outer + vi for vi in reversed(f)])
        edge_count: Dict[tuple, int] = {}
        edge_faces: Dict[tuple, List[int]] = {}
        for i, f in enumerate(faces):
            for j in range(len(f)):
                a, b = f[j], f[(j + 1) % len(f)]
                key = tuple(sorted((a, b)))
                edge_count[key] = edge_count.get(key, 0) + 1
                edge_faces.setdefault(key, []).append(i)
        for (a, b), cnt in edge_count.items():
            faces_of_edge = edge_faces.get((a, b), [])
            is_opening_boundary = any(fi in open_indices for fi in faces_of_edge)
            if cnt == 1 or is_opening_boundary:
                result_faces.append([a, b, n_outer + b, n_outer + a])
        return Mesh(vertices=result_verts, faces=result_faces, name=f"{mesh.name}_shell")

    def _resolve_face_indices(self, faces: List[List[int]], verts) -> set:
        open_set = set()
        if not self.faces:
            return open_set
        try:
            import numpy as np
        except ImportError:
            return open_set
        normals = []
        for f in faces:
            if len(f) >= 3:
                v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
                normals.append(np.cross(v1 - v0, v2 - v0))
            else:
                normals.append(np.zeros(3))
        normals = np.asarray(normals)
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        unit_normals = normals / norms
        named_map = {
            "top": np.array([0.0, 1.0, 0.0]), "bottom": np.array([0.0, -1.0, 0.0]),
            "front": np.array([0.0, 0.0, 1.0]), "back": np.array([0.0, 0.0, -1.0]),
            "right": np.array([1.0, 0.0, 0.0]), "left": np.array([-1.0, 0.0, 0.0]),
        }
        for sel in self.faces:
            if isinstance(sel, int):
                if 0 <= sel < len(faces):
                    open_set.add(sel)
            elif isinstance(sel, str):
                if sel.isdigit():
                    idx = int(sel)
                    if 0 <= idx < len(faces):
                        open_set.add(idx)
                elif sel.lower() in named_map:
                    target = named_map[sel.lower()]
                    dots = unit_normals @ target
                    best = int(np.argmax(dots))
                    if dots[best] > 0.5:
                        open_set.add(best)
        return open_set
