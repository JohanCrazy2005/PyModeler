"""Additional features: Fillet, Chamfer, FeatureHistory."""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional
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
    ExtrudeFeature,
    RevolveFeature,
    HoleFeature,
)

class FilletFeature:
    """Parametric Fillet feature stub.

    Stores radius and optional edge selection. Full rolling-ball mesh fillet is deferred.
    generate_mesh returns a small placeholder sphere whose radius matches the fillet radius
    so the feature is visible in the timeline / recompute path.
    """

    def __init__(
        self,
        radius: float | str = 1.0,
        name: str = "Fillet",
        edges: Optional[list] = None,
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
            edges=data.get("edges", []),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_radius(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.radius, parameters, 1.0)

    def generate_mesh(self, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Placeholder mesh for timeline visibility when no base body is available."""
        r = self.resolved_radius(parameters)
        if r <= 0:
            raise FeatureValidationError("Fillet radius must be positive")
        from .mesh import create_sphere
        return create_sphere(radius=r, name=self.id)

    def apply_to_mesh(self, base: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Apply a basic multi-segment edge bevel approximating a fillet on *base*."""
        r = self.resolved_radius(parameters)
        if r <= 0:
            raise FeatureValidationError("Fillet radius must be positive")
        edges = self.edges if self.edges else None
        # segments=4 gives a coarse rounded look
        return base.bevel_edges(edges=edges, amount=r, segments=4, name=f"{base.name}_fillet")


class ChamferFeature:
    """Parametric Chamfer feature.

    Supports equal-distance, two-distance, and distance-and-angle modes.
    generate_mesh returns a small placeholder cone.
    apply_to_mesh uses Mesh.bevel_edges (basic approximation).
    """

    def __init__(
        self,
        distance: float | str = 1.0,
        name: str = "Chamfer",
        edges: Optional[list] = None,
        operation: str = "modify",
        mode: str = "equal_distance",
        distance2: float | str | None = None,
        angle: float | str | None = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("chamfer")
        self.type = "chamfer"
        self.name = name
        self.distance = distance
        self.mode = mode
        self.distance2 = distance2
        self.angle = angle
        self.edges = edges or []
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "distance": self.distance,
            "mode": self.mode,
            "edges": self.edges,
            "operation": self.operation,
        }
        if self.distance2 is not None:
            data["distance2"] = self.distance2
        if self.angle is not None:
            data["angle"] = self.angle
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
            edges=data.get("edges", []),
            operation=data.get("operation", "modify"),
            mode=data.get("mode", "equal_distance"),
            distance2=data.get("distance2"),
            angle=data.get("angle"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_distance(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.distance, parameters, 1.0)

    def resolved_distance2(self, parameters: Optional[ParameterStore] = None) -> Optional[float]:
        if self.distance2 is None:
            return None
        return _resolve_value(self.distance2, parameters, 1.0)

    def resolved_angle(self, parameters: Optional[ParameterStore] = None) -> Optional[float]:
        if self.angle is None:
            return None
        return _resolve_value(self.angle, parameters, 45.0)

    def generate_mesh(self, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Placeholder mesh for timeline visibility when no base body is available."""
        d = self.resolved_distance(parameters)
        if d <= 0:
            raise FeatureValidationError("Chamfer distance must be positive")
        from .mesh import create_cone
        mesh = create_cone(radius=d, height=d * 0.5, name=self.id)
        return mesh

    def apply_to_mesh(self, base: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Apply a basic edge bevel on *base*, honoring the chamfer mode."""
        d1 = self.resolved_distance(parameters)
        if d1 <= 0:
            raise FeatureValidationError("Chamfer distance must be positive")
        d2 = self.resolved_distance2(parameters)
        ang = self.resolved_angle(parameters)
        edges = self.edges if self.edges else None

        if self.mode == "two_distance" and d2 is not None:
            return base.bevel_edges(
                edges=edges, amount=d1, amount2=d2, segments=1, name=f"{base.name}_chamfer"
            )
        elif self.mode == "distance_angle" and ang is not None:
            # Approximate second distance from angle (simple tan relation for stub)
            d2_approx = d1 * abs(math.tan(math.radians(ang))) if ang != 90 else d1
            return base.bevel_edges(
                edges=edges, amount=d1, amount2=d2_approx, segments=1, name=f"{base.name}_chamfer"
            )
        else:
            # equal_distance or fallback
            return base.bevel_edges(edges=edges, amount=d1, segments=1, name=f"{base.name}_chamfer")


class ShellFeature:
    """Parametric Shell feature.

    Stores thickness, optional faces to remove, and direction.
    apply_to_mesh builds a basic hollow approximation by offsetting
    vertices along normals and connecting walls (mesh shell).
    generate_mesh returns a small placeholder box whose size reflects thickness
    so the feature is visible in the timeline / recompute path when no body exists.
    """

    def __init__(
        self,
        thickness: float | str = 1.0,
        name: str = "Shell",
        faces: Optional[list] = None,
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
        self.direction = direction
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
            faces=data.get("faces", []),
            direction=data.get("direction", "inside"),
            operation=data.get("operation", "modify"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_thickness(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.thickness, parameters, 1.0)

    def _resolve_open_faces(self, base: Mesh) -> set:
        """Map self.faces (int indices and/or named labels) to a set of face indices.

        Supported names (case-insensitive): top, bottom, front, back, left, right.
        Mapping uses the dominant axis of each face normal.
        """
        import numpy as np
        open_faces: set = set()
        name_map: dict[str, int] = {}
        # Build name -> best face index by normal
        best: dict[str, tuple[float, int]] = {}
        for fi, face in enumerate(base.faces):
            try:
                n = np.asarray(base.compute_face_normal(fi), dtype=float)
            except Exception:
                continue
            length = float(np.linalg.norm(n))
            if length < 1e-12:
                continue
            n = n / length
            ax = int(np.argmax(np.abs(n)))
            sign = 1.0 if n[ax] >= 0 else -1.0
            score = abs(float(n[ax]))
            if ax == 2:
                label = "top" if sign > 0 else "bottom"
            elif ax == 1:
                label = "back" if sign > 0 else "front"
            else:
                label = "right" if sign > 0 else "left"
            prev = best.get(label)
            if prev is None or score > prev[0]:
                best[label] = (score, fi)
        name_map = {k: v[1] for k, v in best.items()}

        for f in self.faces:
            if isinstance(f, int):
                if 0 <= f < len(base.faces):
                    open_faces.add(f)
            elif isinstance(f, str):
                key = f.strip().lower()
                if key in name_map:
                    open_faces.add(name_map[key])
                else:
                    # Try integer-as-string
                    try:
                        idx = int(key)
                        if 0 <= idx < len(base.faces):
                            open_faces.add(idx)
                    except ValueError:
                        pass
        return open_faces

    def generate_mesh(self, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Placeholder mesh for timeline visibility when no base body is available."""
        t = self.resolved_thickness(parameters)
        if t <= 0:
            raise FeatureValidationError("Shell thickness must be positive")
        from .mesh import create_cube
        # Scale placeholder by thickness so it is visible
        return create_cube(size=max(t * 2.0, 0.5), name=self.id)

    def apply_to_mesh(self, base: Mesh, parameters: Optional[ParameterStore] = None) -> Mesh:
        """Basic mesh shell approximation with corner mitering.

        Creates an inner (or outer) offset surface by moving vertices along
        averaged face normals, scaled by a miter factor so wall thickness is
        more uniform at sharp corners. Then builds connecting wall faces between
        the original and offset surfaces. This produces a hollow solid with
        approximately constant wall thickness.

        Faces listed in self.faces (integer indices or named labels such as
        "top"/"bottom"/"front"/"back"/"left"/"right") are treated as openings:
        they are omitted from the outer and inner surfaces. Boundary edges of
        openings receive explicit rim walls so the shell thickness is visible
        at the lip.

        Direction:
          - inside  : offset inward (outer dimensions preserved)
          - outside : offset outward (part grows)
          - both    : creates both an inner and an outer offset and connects
                      them (approximate)

        Falls back to a simple centroid-scaled Boolean-style wall if the
        normal-offset path produces an invalid mesh.
        """
        import numpy as np
        from collections import defaultdict

        t = self.resolved_thickness(parameters)
        if t <= 0:
            raise FeatureValidationError("Shell thickness must be positive")

        if not base.vertices or not base.faces:
            return Mesh(vertices=list(base.vertices), faces=list(base.faces), name=f"{base.name}_shell")

        direction = self.direction
        # Resolve face identifiers (integer indices or named labels) into opening set.
        # Named labels: "top"/"bottom"/"front"/"back"/"left"/"right" mapped by face
        # normal direction (largest absolute component of the face normal).
        open_faces = self._resolve_open_faces(base)

        # Compute per-vertex normal (average of adjacent face normals)
        # and a miter scale so the offset approximates constant wall thickness
        # at sharp corners (offset distance along bisector is larger).
        vert_normals = [np.zeros(3) for _ in base.vertices]
        vert_face_count = [0 for _ in base.vertices]
        face_normals = []
        for fi, face in enumerate(base.faces):
            n = np.asarray(base.compute_face_normal(fi), dtype=float)
            face_normals.append(n)
            for vi in face:
                vert_normals[vi] += n
                vert_face_count[vi] += 1
        miter_scales = [1.0] * len(base.vertices)
        for i, n in enumerate(vert_normals):
            length = np.linalg.norm(n)
            if length > 1e-8:
                vert_normals[i] = n / length
            else:
                vert_normals[i] = np.array([0.0, 0.0, 1.0])
            # Average 1 / (vn · nf) over adjacent faces to miter the corner
            if vert_face_count[i] > 0:
                scales = []
                for fi, face in enumerate(base.faces):
                    if i in face:
                        nf = face_normals[fi]
                        dot = float(np.dot(vert_normals[i], nf))
                        if dot > 0.1:  # avoid near-perpendicular or inverted
                            scales.append(1.0 / dot)
                if scales:
                    miter_scales[i] = float(np.mean(scales))
                # Clamp extreme miters to avoid explosions on very sharp corners
                miter_scales[i] = min(miter_scales[i], 4.0)

        # Build offset vertices
        def offset_verts(sign: float, thickness: float) -> list[list[float]]:
            result = []
            for i, v in enumerate(base.vertices):
                scale = miter_scales[i]
                off = np.asarray(v, dtype=float) + sign * thickness * scale * vert_normals[i]
                result.append(off.tolist())
            return result

        if direction == "outside":
            outer_verts = offset_verts(1.0, t)
            inner_verts = [list(v) for v in base.vertices]
            # Reverse roles for consistent winding later
        elif direction == "both":
            outer_verts = offset_verts(1.0, t / 2.0)
            inner_verts = offset_verts(-1.0, t / 2.0)
        else:  # inside (default)
            outer_verts = [list(v) for v in base.vertices]
            inner_verts = offset_verts(-1.0, t)

        # Combine: outer vertices first, then inner
        all_verts = outer_verts + inner_verts
        n_outer = len(outer_verts)

        new_faces: list[list[int]] = []

        # Outer faces (skip openings)
        for fi, face in enumerate(base.faces):
            if fi in open_faces:
                continue
            new_faces.append(list(face))  # same winding, points outward

        # Inner faces (reversed winding so they point inward / consistent for hollow)
        for fi, face in enumerate(base.faces):
            if fi in open_faces:
                continue
            reversed_face = [n_outer + vi for vi in reversed(face)]
            new_faces.append(reversed_face)

        # Wall faces along every edge (connecting outer to inner).
        # Include edges from kept faces (side walls) AND edges of open faces
        # so openings get explicit rim walls (lip of the shell thickness).
        edge_dir: dict[tuple[int, int], tuple[int, int]] = {}
        for fi, face in enumerate(base.faces):
            m = len(face)
            for i in range(m):
                a, b = face[i], face[(i + 1) % m]
                key = (min(a, b), max(a, b))
                # Prefer directed edge from a non-open face when both share the edge
                if key not in edge_dir or fi not in open_faces:
                    edge_dir[key] = (a, b)

        for (a, b), (da, db) in edge_dir.items():
            # Outer edge da->db, inner corresponding
            na, nb = n_outer + da, n_outer + db
            # Quad with consistent outward-ish winding
            new_faces.append([da, db, nb, na])

        try:
            result = Mesh(
                vertices=all_verts,
                faces=new_faces,
                name=f"{base.name}_shell",
            )
            return result
        except Exception:
            # Fallback: simple scaled copy (still different from original)
            return Mesh(
                vertices=[[c * 0.9 for c in v] for v in base.vertices],
                faces=list(base.faces),
                name=f"{base.name}_shell",
            )


class FeatureHistory:
    """Ordered timeline of features with rollback support."""

    def __init__(
        self,
        name: str = "Feature History",
        features: Optional[List[dict]] = None,
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
            name=data.get("name", "Feature History"),
            features=data.get("features", []),
            rollback_marker=data.get("rollback_marker"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add_extrude(self, feat: ExtrudeFeature) -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_revolve(self, feat: RevolveFeature) -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_hole(self, feat: "HoleFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_fillet(self, feat: "FilletFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_chamfer(self, feat: "ChamferFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def add_shell(self, feat: "ShellFeature") -> None:
        self.features.append(feat.to_dict())
        self.validate()

    def active_features(self) -> List[dict]:
        if self.rollback_marker is None:
            return list(self.features)
        return list(self.features[: self.rollback_marker + 1])

    def recompute_meshes(self, sketches, params=None):
        result = {}
        for fdict in self.active_features():
            ftype = fdict.get("type")
            if ftype == "extrude":
                feat = ExtrudeFeature.from_dict(fdict)
                result[feat.id] = feat.generate_mesh(sketches, params)
            elif ftype == "revolve":
                feat = RevolveFeature.from_dict(fdict)
                result[feat.id] = feat.generate_mesh(sketches, params)
            elif ftype == "hole":
                feat = HoleFeature.from_dict(fdict)
                result[feat.id] = feat.generate_mesh(params)
            elif ftype == "fillet":
                feat = FilletFeature.from_dict(fdict)
                result[feat.id] = feat.generate_mesh(params)
            elif ftype == "chamfer":
                feat = ChamferFeature.from_dict(fdict)
                result[feat.id] = feat.generate_mesh(params)
            elif ftype == "shell":
                feat = ShellFeature.from_dict(fdict)
                result[feat.id] = feat.generate_mesh(params)
        return result
