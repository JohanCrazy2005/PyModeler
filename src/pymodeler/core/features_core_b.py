"""RevolveFeature and HoleFeature (through_all support)."""
from __future__ import annotations
import math
from typing import Any, Optional
from .mesh import Mesh
from .parameters import ParameterStore
from .sketch import Sketch, extract_simple_profiles
from .features_core_a import (
    FeatureValidationError, validate_revolve_data, validate_hole_data, _new_id, _resolve_value,
)

class RevolveFeature:
    def __init__(self, sketch_id: str, angle: float | str = 360.0, name: str = "Revolve",
                 axis=None, axis_origin=None, symmetric: bool = False, operation: str = "new",
                 segments: int = 16, metadata=None, id: Optional[str] = None):
        self.id = id or _new_id("revolve")
        self.type = "revolve"
        self.name = name
        self.sketch_id = sketch_id
        self.angle = angle
        self.axis = axis
        self.axis_origin = axis_origin
        self.symmetric = symmetric
        self.operation = operation
        self.segments = segments
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data = {"id": self.id, "type": self.type, "name": self.name, "sketch_id": self.sketch_id,
                "angle": self.angle, "symmetric": self.symmetric, "operation": self.operation,
                "segments": self.segments}
        if self.axis is not None:
            data["axis"] = self.axis
        if self.axis_origin is not None:
            data["axis_origin"] = self.axis_origin
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_revolve_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "RevolveFeature":
        validate_revolve_data(data)
        return cls(sketch_id=data["sketch_id"], angle=data["angle"], name=data.get("name", "Revolve"),
                   axis=data.get("axis"), axis_origin=data.get("axis_origin"),
                   symmetric=data.get("symmetric", False), operation=data.get("operation", "new"),
                   segments=data.get("segments", 16), metadata=data.get("metadata"), id=data.get("id"))

    def resolved_angle(self, parameters=None) -> float:
        return _resolve_value(self.angle, parameters, 360.0)

    def generate_mesh(self, sketch: Sketch, parameters=None) -> Mesh:
        angle = self.resolved_angle(parameters)
        if angle <= 0 or angle > 360:
            raise FeatureValidationError("Revolve angle must be in (0, 360]")
        profiles = extract_simple_profiles(sketch)
        segs = max(4, min(64, self.segments))
        if not profiles:
            from .mesh import create_cylinder
            return create_cylinder(radius=1.0, height=2.0, segments=segs, name=self.id)
        prof = profiles[0]
        if prof["type"] == "polygon" and prof.get("points"):
            mesh = self._revolve_polygon(prof["points"], angle, segs)
            return self._apply_axis_transform(mesh)
        from .mesh import create_cylinder
        xs = []
        for p in profiles:
            if p["type"] == "polygon":
                xs.extend(x for x, _ in p["points"])
            elif p["type"] == "circle":
                xs.append(p["center"][0] + p["radius"])
        radius = max((abs(x) for x in xs), default=1.0) or 1.0
        return create_cylinder(radius=radius, height=2.0, segments=segs, name=self.id)

    def _revolve_polygon(self, points, angle_deg: float, segs: int) -> Mesh:
        if len(points) < 3:
            from .mesh import create_cylinder
            return create_cylinder(radius=1.0, height=1.0, segments=segs, name=self.id)
        pts = [(float(x), float(y)) for x, y in points]
        n_profile = len(pts)
        angle_rad = math.radians(angle_deg)
        full = abs(angle_deg - 360.0) < 1e-3
        n_angle = segs if full else max(2, int(segs * angle_deg / 360.0))
        n_angle = max(2, min(64, n_angle))
        verts = []
        for x, y in pts:
            r = abs(x)
            for j in range(n_angle + (0 if full else 1)):
                theta = 2 * math.pi * j / n_angle if full else angle_rad * j / max(1, n_angle)
                verts.append([r * math.cos(theta), y, r * math.sin(theta)])
        faces = []
        ring_size = n_angle if full else n_angle + 1
        for i in range(n_profile):
            ni = (i + 1) % n_profile
            for j in range(n_angle):
                a = i * ring_size + j
                b = i * ring_size + ((j + 1) % ring_size if full else j + 1)
                c = ni * ring_size + ((j + 1) % ring_size if full else j + 1)
                d = ni * ring_size + j
                faces.append([a, b, c, d])
        if not full and n_angle >= 1:
            faces.append([i * ring_size for i in range(n_profile)])
            faces.append([i * ring_size + n_angle for i in range(n_profile - 1, -1, -1)])
        return Mesh(vertices=verts, faces=faces, name=self.id)



    def _apply_axis_transform(self, mesh: Mesh) -> Mesh:
        """Rotate the Y-axis revolve result so the axis matches self.axis (default Y)."""
        if not self.axis:
            return mesh
        try:
            import numpy as np
            axis = np.asarray(self.axis, dtype=float)
            norm = np.linalg.norm(axis)
            if norm < 1e-8:
                return mesh
            axis = axis / norm
            # Rotation that takes Y-axis to the given axis
            y = np.array([0.0, 1.0, 0.0])
            if np.allclose(axis, y):
                return mesh
            # Rodrigues formula
            k = np.cross(y, axis)
            k_norm = np.linalg.norm(k)
            if k_norm < 1e-8:
                # 180 degree case
                R = np.diag([-1.0, 1.0, -1.0])
            else:
                k = k / k_norm
                cos_t = float(np.dot(y, axis))
                sin_t = k_norm
                K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
                R = np.eye(3) + sin_t * K + (1 - cos_t) * (K @ K)
            origin = np.asarray(self.axis_origin or [0.0, 0.0, 0.0], dtype=float)
            verts = []
            for v in mesh.vertices:
                p = np.asarray(v, dtype=float)
                verts.append((R @ p + origin).tolist())
            mesh.vertices = verts
            mesh.validate()
            return mesh
        except Exception:
            return mesh

class HoleFeature:
    """Parametric Hole with blind or through_all extents."""
    DEFAULT_THROUGH_DEPTH = 1000.0

    def __init__(self, diameter: float | str = 1.0, depth: float | str | None = 1.0, name: str = "Hole",
                 center=None, direction=None, segments: int = 24, operation: str = "cut",
                 extent: str = "blind", through_depth: float | str | None = None,
                 metadata=None, id: Optional[str] = None):
        self.id = id or _new_id("hole")
        self.type = "hole"
        self.name = name
        self.diameter = diameter
        self.depth = 1.0 if depth is None else depth
        self.center = center
        self.direction = direction
        self.segments = segments
        self.operation = operation
        self.extent = extent if extent in ("blind", "through_all") else "blind"
        self.through_depth = through_depth
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id, "type": self.type, "name": self.name, "diameter": self.diameter,
            "depth": self.depth, "segments": self.segments, "operation": self.operation, "extent": self.extent,
        }
        if self.through_depth is not None:
            data["through_depth"] = self.through_depth
        if self.center is not None:
            data["center"] = self.center
        if self.direction is not None:
            data["direction"] = self.direction
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_hole_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "HoleFeature":
        validate_hole_data(data)
        return cls(diameter=data["diameter"], depth=data.get("depth", 1.0), name=data.get("name", "Hole"),
                   center=data.get("center"), direction=data.get("direction"),
                   segments=data.get("segments", 24), operation=data.get("operation", "cut"),
                   extent=data.get("extent", "blind"), through_depth=data.get("through_depth"),
                   metadata=data.get("metadata"), id=data.get("id"))

    def resolved_diameter(self, parameters=None) -> float:
        return _resolve_value(self.diameter, parameters, 1.0)

    def resolved_depth(self, parameters=None) -> float:
        return _resolve_value(self.depth, parameters, 1.0)

    def resolved_through_depth(self, parameters=None) -> float:
        if self.through_depth is None:
            return self.DEFAULT_THROUGH_DEPTH
        return _resolve_value(self.through_depth, parameters, self.DEFAULT_THROUGH_DEPTH)

    def generate_mesh(self, parameters=None) -> Mesh:
        diam = self.resolved_diameter(parameters)
        if diam <= 0:
            raise FeatureValidationError("Hole diameter must be positive")
        if self.extent == "through_all":
            depth = self.resolved_through_depth(parameters)
            if depth <= 0:
                raise FeatureValidationError("through_depth must be positive for through_all holes")
            center_on_start = True
        else:
            depth = self.resolved_depth(parameters)
            if depth <= 0:
                raise FeatureValidationError("Hole depth must be positive for blind holes")
            center_on_start = False
        radius = diam / 2.0
        segs = max(3, min(128, self.segments))
        from .mesh import create_cylinder
        import numpy as np
        mesh = create_cylinder(radius=radius, height=depth, segments=segs, name=self.id)
        verts = np.asarray(mesh.vertices, dtype=float)
        if not center_on_start:
            verts[:, 1] -= float(verts[:, 1].min())
        cx = cy = cz = 0.0
        if self.center:
            cx, cy = float(self.center[0]), float(self.center[1])
            if len(self.center) > 2:
                cz = float(self.center[2])
        verts[:, 0] += cx
        verts[:, 2] += cy
        verts[:, 1] += cz
        mesh.vertices = verts.tolist()
        mesh.validate()
        return mesh
