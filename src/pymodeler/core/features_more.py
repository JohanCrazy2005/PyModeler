"""Additional features: Fillet, Chamfer, Shell, FeatureHistory.

ShellFeature includes an optional Boolean-based offset path when a Boolean
engine (trimesh + manifold3d) is available. Closed inside shells prefer
Boolean difference of an inward-offset solid for cleaner topology; any failure
falls back to the wall-stitching approximation.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from .mesh import Mesh
from .parameters import ParameterStore
from .features_core import (
    FeatureValidationError,
    validate_fillet_data,
    validate_chamfer_data,
    validate_shell_data,
    validate_history_data,
    _new_id,
    _resolve_value,
)


class FilletFeature:
    """Parametric Fillet stub. apply_to_mesh currently returns the mesh unchanged."""

    def __init__(
        self,
        radius: float | str = 1.0,
        name: str = "Fillet",
        edges: Optional[List] = None,
        operation: str = "modify",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("fillet")
        self.type = "fillet"
        self.name = name
        self.radius = radius
        self.edges = edges or []
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "radius": self.radius,
            "edges": self.edges,
            "operation": self.operation,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_fillet_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "FilletFeature":
        validate_fillet_data(data)
        return cls(
            radius=data["radius"],
            name=data.get("name", "Fillet"),
            edges=data.get("edges"),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_radius(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.radius, parameters, 1.0)

    def apply_to_mesh(self, mesh: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        # Stub: full rolling-ball fillet deferred. Return original mesh.
        return mesh


class ChamferFeature:
    """Parametric Chamfer stub. apply_to_mesh currently returns the mesh unchanged."""

    def __init__(
        self,
        distance: float | str = 1.0,
        name: str = "Chamfer",
        edges: Optional[List] = None,
        mode: str = "equal",
        secondary: Optional[float | str] = None,
        operation: str = "modify",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("chamfer")
        self.type = "chamfer"
        self.name = name
        self.distance = distance
        self.edges = edges or []
        self.mode = mode
        self.secondary = secondary
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "distance": self.distance,
            "edges": self.edges,
            "mode": self.mode,
            "operation": self.operation,
        }
        if self.secondary is not None:
            data["secondary"] = self.secondary
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_chamfer_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ChamferFeature":
        validate_chamfer_data(data)
        return cls(
            distance=data["distance"],
            name=data.get("name", "Chamfer"),
            edges=data.get("edges"),
            mode=data.get("mode", "equal"),
            secondary=data.get("secondary"),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def apply_to_mesh(self, mesh: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        # Stub: full chamfer deferred. Return original mesh.
        return mesh


class ShellFeature:
    """Parametric Shell feature with optional Boolean-based offset.

    For closed shells (no faces selected) with direction='inside', attempts a
    Boolean cut of an inward-offset solid when a Boolean engine is available.
    Falls back to wall-stitching on any failure. Openings and other directions
    use the wall-stitching approximation.
    """

    def __init__(
        self,
        thickness: float | str = 1.0,
        name: str = "Shell",
        faces: Optional[List] = None,
        direction: str = "inside",
        operation: str = "modify",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
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
        data: dict[str, Any] = {
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
        return _resolve_value(self.thickness, parameters, 1.0)

    def apply_to_mesh(self, mesh: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        thickness = self.resolved_thickness(parameters)
        if thickness <= 0:
            raise FeatureValidationError("Shell thickness must be positive")

        # Prefer Boolean path for closed inside shells when engine available
        if not self.faces and self.direction == "inside":
            try:
                result = self._boolean_shell(mesh, thickness)
                if result is not None and result.faces:
                    return result
            except Exception:
                pass  # fall through to wall method

        return self._wall_stitch_shell(mesh, thickness)

    def _boolean_shell(self, mesh: Mesh, thickness: float) -> Optional[Mesh]:
        """Create inner offset solid and Boolean-cut it from the original.

        Returns the hollow solid or None if the operation cannot be performed.
        """
        try:
            from .boolean import mesh_boolean
        except Exception:
            return None

        inner = self._offset_mesh_inward(mesh, thickness)
        if inner is None or not inner.faces:
            return None

        try:
            result = mesh_boolean(mesh, inner, "cut", name=f"{mesh.name}_shell")
            return result
        except Exception:
            return None

    def _offset_mesh_inward(self, mesh: Mesh, thickness: float) -> Optional[Mesh]:
        """Simple inward offset: scale vertices toward centroid by thickness.

        This is an approximation; true constant-thickness offset requires a better kernel.
        """
        try:
            import numpy as np
        except ImportError:
            return None

        verts = np.asarray(mesh.vertices, dtype=float)
        if len(verts) < 4:
            return None
        centroid = verts.mean(axis=0)
        # Compute average distance from centroid for scale factor
        dists = np.linalg.norm(verts - centroid, axis=1)
        avg_dist = float(dists.mean()) if len(dists) else 1.0
        if avg_dist < 1e-8:
            return None
        # Scale so that surfaces move inward by approximately thickness
        scale = max(0.1, (avg_dist - thickness) / avg_dist)
        new_verts = centroid + (verts - centroid) * scale
        # Reverse winding for inner solid (or keep and let Boolean handle)
        faces = [list(f) for f in mesh.faces]
        return Mesh(vertices=new_verts.tolist(), faces=faces, name=f"{mesh.name}_inner")

    def _wall_stitch_shell(self, mesh: Mesh, thickness: float) -> Mesh:
        """Fallback wall-stitching approximation: outer + offset inner + walls.

        Supports simple openings (integer face indices omitted) and named faces.
        """
        try:
            import numpy as np
        except ImportError:
            return mesh

        verts = np.asarray(mesh.vertices, dtype=float)
        faces = [list(f) for f in mesh.faces]
        n_faces = len(faces)
        if n_faces == 0 or len(verts) == 0:
            return mesh

        # Resolve opening faces
        open_indices = self._resolve_face_indices(faces, verts)

        # Compute per-face normals
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

        # Vertex normals (area-weighted average of adjacent faces)
        v_normals = np.zeros_like(verts)
        for i, f in enumerate(faces):
            for vi in f:
                if 0 <= vi < len(verts):
                    v_normals[vi] += normals[i]
        v_norms = np.linalg.norm(v_normals, axis=1, keepdims=True)
        v_norms[v_norms < 1e-12] = 1.0
        v_normals /= v_norms

        # Offset direction
        sign = -1.0 if self.direction == "inside" else 1.0
        if self.direction == "both":
            sign = 0.0  # handled specially below; for simplicity use half

        offset_dist = thickness if self.direction != "both" else thickness / 2.0
        inner_verts = verts + sign * offset_dist * v_normals

        # Build result: outer faces (skip openings) + inner faces (reversed, skip openings) + walls
        result_verts = verts.tolist() + inner_verts.tolist()
        n_outer = len(verts)
        result_faces: List[List[int]] = []

        # Outer surface
        for i, f in enumerate(faces):
            if i not in open_indices:
                result_faces.append(f)

        # Inner surface (reversed winding, offset indices)
        for i, f in enumerate(faces):
            if i not in open_indices:
                result_faces.append([n_outer + vi for vi in reversed(f)])

        # Connecting walls on boundary edges of openings or all edges if closed
        # Simple: for every edge of non-open faces, if the edge is shared with an open face or is boundary, add a wall
        edge_count: Dict[tuple, int] = {}
        edge_faces: Dict[tuple, List[int]] = {}
        for i, f in enumerate(faces):
            for j in range(len(f)):
                a, b = f[j], f[(j + 1) % len(f)]
                key = tuple(sorted((a, b)))
                edge_count[key] = edge_count.get(key, 0) + 1
                edge_faces.setdefault(key, []).append(i)

        for (a, b), cnt in edge_count.items():
            # Add wall if boundary or adjacent to an opening
            faces_of_edge = edge_faces.get((a, b), [])
            is_opening_boundary = any(fi in open_indices for fi in faces_of_edge)
            if cnt == 1 or is_opening_boundary:
                # Quad wall: a -> b -> b_inner -> a_inner
                result_faces.append([a, b, n_outer + b, n_outer + a])

        return Mesh(vertices=result_verts, faces=result_faces, name=f"{mesh.name}_shell")

    def _resolve_face_indices(self, faces: List[List[int]], verts) -> set:
        """Resolve face selection (indices or named: top/bottom/front/back/left/right)."""
        open_set = set()
        if not self.faces:
            return open_set
        try:
            import numpy as np
        except ImportError:
            return open_set

        # Compute dominant axis for named faces
        normals = []
        for f in faces:
            if len(f) >= 3:
                v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
                n = np.cross(v1 - v0, v2 - v0)
                normals.append(n)
            else:
                normals.append(np.zeros(3))
        normals = np.asarray(normals)
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        unit_normals = normals / norms

        named_map = {
            "top": np.array([0.0, 1.0, 0.0]),
            "bottom": np.array([0.0, -1.0, 0.0]),
            "front": np.array([0.0, 0.0, 1.0]),
            "back": np.array([0.0, 0.0, -1.0]),
            "right": np.array([1.0, 0.0, 0.0]),
            "left": np.array([-1.0, 0.0, 0.0]),
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


class FeatureHistory:
    """Ordered timeline of parametric features with rollback support."""

    def __init__(
        self,
        features: Optional[List[dict]] = None,
        name: str = "Feature History",
        rollback_marker: Optional[int] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("hist")
        self.name = name
        self.features: List[dict] = features or []
        self.rollback_marker = rollback_marker
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "features": self.features,
        }
        if self.rollback_marker is not None:
            data["rollback_marker"] = self.rollback_marker
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_history_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureHistory":
        validate_history_data(data)
        return cls(
            features=data.get("features"),
            name=data.get("name", "Feature History"),
            rollback_marker=data.get("rollback_marker"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add(self, feature_dict: dict) -> None:
        self.features.append(feature_dict)
        self.validate()

    def active_features(self) -> List[dict]:
        if self.rollback_marker is None:
            return list(self.features)
        marker = max(0, min(self.rollback_marker, len(self.features)))
        return self.features[:marker]

    def recompute_meshes(self, sketches: dict, parameters: Optional[ParameterStore] = None) -> Dict[str, Mesh]:
        """Recompute independent geometry for active features that produce meshes."""
        from .features import ExtrudeFeature, RevolveFeature, HoleFeature

        result: Dict[str, Mesh] = {}
        for fdict in self.active_features():
            ftype = fdict.get("type")
            fid = fdict.get("id", "feat")
            try:
                if ftype == "extrude":
                    feat = ExtrudeFeature.from_dict(fdict)
                    sketch = sketches.get(feat.sketch_id)
                    if sketch:
                        result[fid] = feat.generate_mesh(sketch, parameters)
                elif ftype == "revolve":
                    feat = RevolveFeature.from_dict(fdict)
                    sketch = sketches.get(feat.sketch_id)
                    if sketch:
                        result[fid] = feat.generate_mesh(sketch, parameters)
                elif ftype == "hole":
                    feat = HoleFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(parameters)
            except Exception:
                continue
        return result
