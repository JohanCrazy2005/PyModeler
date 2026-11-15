"""Parametric features (Extrude, Revolve, etc.) and feature history.

ExtrudeFeature turns a Sketch into a solid mesh driven by a numeric distance
or a ParameterStore reference. RevolveFeature rotates a profile around an axis.
FeatureHistory is a serializable timeline.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import jsonschema
from jsonschema import Draft202012Validator

from .mesh import Mesh
from .parameters import ParameterStore
from .sketch import Sketch

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_EXTRUDE_SCHEMA_PATH = _SCHEMA_DIR / "extrude.schema.json"
_REVOLVE_SCHEMA_PATH = _SCHEMA_DIR / "revolve.schema.json"
_HISTORY_SCHEMA_PATH = _SCHEMA_DIR / "feature_history.schema.json"

with open(_EXTRUDE_SCHEMA_PATH, encoding="utf-8") as f:
    EXTRUDE_SCHEMA = json.load(f)
with open(_REVOLVE_SCHEMA_PATH, encoding="utf-8") as f:
    REVOLVE_SCHEMA = json.load(f)
with open(_HISTORY_SCHEMA_PATH, encoding="utf-8") as f:
    HISTORY_SCHEMA = json.load(f)

_EXTRUDE_VALIDATOR = Draft202012Validator(EXTRUDE_SCHEMA)
_REVOLVE_VALIDATOR = Draft202012Validator(REVOLVE_SCHEMA)
_HISTORY_VALIDATOR = Draft202012Validator(HISTORY_SCHEMA)


class FeatureValidationError(ValueError):
    """Raised when feature or history data fails schema validation."""


def validate_extrude_data(data: dict) -> None:
    errors = sorted(_EXTRUDE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Extrude schema validation failed:\n" + "\n".join(messages))


def validate_revolve_data(data: dict) -> None:
    errors = sorted(_REVOLVE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Revolve schema validation failed:\n" + "\n".join(messages))


def validate_history_data(data: dict) -> None:
    errors = sorted(_HISTORY_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("FeatureHistory schema validation failed:\n" + "\n".join(messages))


def _new_id(prefix: str = "feat") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _resolve_distance(distance: float | str, parameters: Optional[ParameterStore] = None) -> float:
    """Resolve a distance that may be numeric or a parameter name / simple expression."""
    if isinstance(distance, (int, float)):
        return float(distance)
    if not isinstance(distance, str) or not distance.strip():
        raise FeatureValidationError("Distance must be a number or non-empty string")
    # Try as bare parameter name first
    if parameters is not None and parameters.get(distance) is not None:
        return parameters.evaluate(distance)
    # Fall back to evaluating as an expression if it looks like one
    if parameters is not None:
        try:
            # Re-use ParameterStore evaluation by temporary param
            tmp_name = "__tmp_dist__"
            if parameters.get(tmp_name) is None:
                parameters.add(tmp_name, expression=distance)
            try:
                return parameters.evaluate(tmp_name)
            finally:
                parameters.remove(tmp_name)
        except Exception:
            pass
    # Last resort: try float conversion
    try:
        return float(distance)
    except ValueError as e:
        raise FeatureValidationError(f"Cannot resolve distance '{distance}'") from e


class ExtrudeFeature:
    """Schema-compliant Extrude feature driven by a Sketch and a distance."""

    def __init__(
        self,
        sketch_id: str,
        distance: float | str,
        name: str = "Extrude",
        direction: Optional[Sequence[float]] = None,
        symmetric: bool = False,
        operation: str = "new",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("extrude")
        self.type = "extrude"
        self.name = name
        self.sketch_id = sketch_id
        self.distance = distance
        self.direction = list(direction) if direction is not None else None
        self.symmetric = bool(symmetric)
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "sketch_id": self.sketch_id,
            "distance": self.distance,
        }
        if self.name != "Extrude":
            data["name"] = self.name
        if self.direction is not None:
            data["direction"] = self.direction
        if self.symmetric:
            data["symmetric"] = self.symmetric
        if self.operation != "new":
            data["operation"] = self.operation
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_extrude_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ExtrudeFeature":
        validate_extrude_data(data)
        return cls(
            sketch_id=data["sketch_id"],
            distance=data["distance"],
            name=data.get("name", "Extrude"),
            direction=data.get("direction"),
            symmetric=data.get("symmetric", False),
            operation=data.get("operation", "new"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_distance(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_distance(self.distance, parameters)

    def generate_mesh(
        self,
        sketch: Sketch,
        parameters: Optional[ParameterStore] = None,
    ) -> Mesh:
        """Generate a simple solid mesh from the sketch + resolved distance.

        Currently supports rectangular sketches created by create_rectangle_sketch
        (four points forming a closed rectangle on the sketch plane).
        Falls back to a unit cube scaled by distance if the profile cannot be
        interpreted as a simple rectangle.
        """
        dist = self.resolved_distance(parameters)
        if dist <= 0:
            raise FeatureValidationError("Extrude distance must be positive")

        # Default direction: sketch plane normal (cross product of axes)
        if self.direction is not None:
            direction = self.direction
        else:
            x_axis = sketch.plane.get("x_axis", [1.0, 0.0, 0.0])
            y_axis = sketch.plane.get("y_axis", [0.0, 1.0, 0.0])
            # Cross product
            direction = [
                x_axis[1] * y_axis[2] - x_axis[2] * y_axis[1],
                x_axis[2] * y_axis[0] - x_axis[0] * y_axis[2],
                x_axis[0] * y_axis[1] - x_axis[1] * y_axis[0],
            ]

        # Try to extract a simple rectangular profile from the sketch
        points = [e for e in sketch.entities if e["type"] == "point"]
        if len(points) >= 4:
            # Collect 2D coords
            coords = [(p["x"], p["y"]) for p in points]
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max_x - min_x
            height = max_y - min_y
            if width > 1e-8 and height > 1e-8:
                # Build a box aligned to the sketch plane
                origin = sketch.plane.get("origin", [0.0, 0.0, 0.0])
                x_axis = sketch.plane.get("x_axis", [1.0, 0.0, 0.0])
                y_axis = sketch.plane.get("y_axis", [0.0, 1.0, 0.0])
                # Normalize direction
                import math
                dlen = math.sqrt(sum(c * c for c in direction)) or 1.0
                d = [c / dlen for c in direction]
                half_dist = dist / 2.0 if self.symmetric else dist

                def to_3d(px: float, py: float, along: float = 0.0) -> list[float]:
                    return [
                        origin[0] + px * x_axis[0] + py * y_axis[0] + along * d[0],
                        origin[1] + px * x_axis[1] + py * y_axis[1] + along * d[1],
                        origin[2] + px * x_axis[2] + py * y_axis[2] + along * d[2],
                    ]

                # Bottom face (z=0 relative) and top face
                bl = to_3d(min_x, min_y, 0.0)
                br = to_3d(max_x, min_y, 0.0)
                tr = to_3d(max_x, max_y, 0.0)
                tl = to_3d(min_x, max_y, 0.0)
                bl2 = to_3d(min_x, min_y, half_dist)
                br2 = to_3d(max_x, min_y, half_dist)
                tr2 = to_3d(max_x, max_y, half_dist)
                tl2 = to_3d(min_x, max_y, half_dist)

                if self.symmetric:
                    # Centered: also go negative
                    bl = to_3d(min_x, min_y, -half_dist)
                    br = to_3d(max_x, min_y, -half_dist)
                    tr = to_3d(max_x, max_y, -half_dist)
                    tl = to_3d(min_x, max_y, -half_dist)

                vertices = [bl, br, tr, tl, bl2, br2, tr2, tl2]
                faces = [
                    [0, 1, 2, 3],  # bottom
                    [4, 5, 6, 7],  # top
                    [0, 1, 5, 4],  # front
                    [2, 3, 7, 6],  # back
                    [0, 3, 7, 4],  # left
                    [1, 2, 6, 5],  # right
                ]
                return Mesh(vertices=vertices, faces=faces, name=self.name or "Extrude")

        # Fallback: unit cube scaled so its height roughly matches distance
        from .mesh import create_cube
        return create_cube(size=dist, name=self.name or "Extrude")


class RevolveFeature:
    """Schema-compliant Revolve feature driven by a Sketch and an angle."""

    def __init__(
        self,
        sketch_id: str,
        angle: float | str,
        name: str = "Revolve",
        axis: Optional[Sequence[float]] = None,
        axis_origin: Optional[Sequence[float]] = None,
        symmetric: bool = False,
        operation: str = "new",
        segments: int = 16,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("revolve")
        self.type = "revolve"
        self.name = name
        self.sketch_id = sketch_id
        self.angle = angle
        self.axis = list(axis) if axis is not None else None
        self.axis_origin = list(axis_origin) if axis_origin is not None else None
        self.symmetric = bool(symmetric)
        self.operation = operation
        self.segments = int(segments)
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "sketch_id": self.sketch_id,
            "angle": self.angle,
        }
        if self.name != "Revolve":
            data["name"] = self.name
        if self.axis is not None:
            data["axis"] = self.axis
        if self.axis_origin is not None:
            data["axis_origin"] = self.axis_origin
        if self.symmetric:
            data["symmetric"] = self.symmetric
        if self.operation != "new":
            data["operation"] = self.operation
        if self.segments != 16:
            data["segments"] = self.segments
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_revolve_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "RevolveFeature":
        validate_revolve_data(data)
        return cls(
            sketch_id=data["sketch_id"],
            angle=data["angle"],
            name=data.get("name", "Revolve"),
            axis=data.get("axis"),
            axis_origin=data.get("axis_origin"),
            symmetric=data.get("symmetric", False),
            operation=data.get("operation", "new"),
            segments=data.get("segments", 16),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_angle(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_distance(self.angle, parameters)  # reuse resolver for numeric/param

    def generate_mesh(
        self,
        sketch: Sketch,
        parameters: Optional[ParameterStore] = None,
    ) -> Mesh:
        """Generate a simple solid-of-revolution mesh from the sketch + resolved angle.

        Currently supports rectangular sketches. Approximates a faceted solid of revolution
        by rotating the rectangle profile around the default Y-axis (or supplied axis).
        Falls back to a simple cylinder-like mesh if the profile cannot be interpreted.
        """
        import math

        angle_deg = self.resolved_angle(parameters)
        if angle_deg <= 0 or angle_deg > 360:
            raise FeatureValidationError("Revolve angle must be in (0, 360] degrees")

        segs = max(4, min(self.segments, 64))
        angle_rad = math.radians(angle_deg)
        if self.symmetric:
            angle_rad /= 2.0

        # Default axis: sketch plane Y-axis
        origin = sketch.plane.get("origin", [0.0, 0.0, 0.0])
        y_axis = sketch.plane.get("y_axis", [0.0, 1.0, 0.0])
        axis_dir = self.axis if self.axis is not None else y_axis
        ax_origin = self.axis_origin if self.axis_origin is not None else origin

        # Normalize axis
        alen = math.sqrt(sum(c * c for c in axis_dir)) or 1.0
        ad = [c / alen for c in axis_dir]

        # Extract simple rectangular profile (same logic as Extrude)
        points = [e for e in sketch.entities if e["type"] == "point"]
        if len(points) >= 4:
            coords = [(p["x"], p["y"]) for p in points]
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            if (max_x - min_x) > 1e-8 and (max_y - min_y) > 1e-8:
                # Profile points in sketch plane (use min/max for a simple rectangle)
                # For revolve we treat X as radial distance from axis, Y as axial height
                # Simple approximation: revolve the outer rectangle around Y
                r_inner = abs(min_x)
                r_outer = abs(max_x)
                h_bot = min_y
                h_top = max_y

                # Build ring of points for bottom and top
                vertices = []
                # Bottom outer / inner, top outer / inner, for each segment
                for i in range(segs + 1):
                    theta = (i / segs) * angle_rad
                    if self.symmetric:
                        theta -= angle_rad  # center it
                    cos_t = math.cos(theta)
                    sin_t = math.sin(theta)
                    # Radial in XZ plane, axial along Y (simplified for default axis)
                    # Offset from ax_origin
                    for r, h in ((r_outer, h_bot), (r_inner, h_bot), (r_outer, h_top), (r_inner, h_top)):
                        # Approximate: assume axis is Y, profile X is radial
                        px = ax_origin[0] + r * cos_t
                        py = ax_origin[1] + h
                        pz = ax_origin[2] + r * sin_t
                        vertices.append([px, py, pz])

                # Build faces (quads between consecutive segments)
                faces = []
                stride = 4  # 4 points per angular step
                for i in range(segs):
                    base = i * stride
                    nxt = (i + 1) * stride
                    # Outer wall
                    faces.append([base + 0, nxt + 0, nxt + 2, base + 2])
                    # Inner wall (if hollow)
                    if r_inner > 1e-6:
                        faces.append([base + 1, base + 3, nxt + 3, nxt + 1])
                    # Bottom annulus
                    faces.append([base + 0, base + 1, nxt + 1, nxt + 0])
                    # Top annulus
                    faces.append([base + 2, nxt + 2, nxt + 3, base + 3])

                # Cap ends if not full 360
                if angle_deg < 359.9:
                    # Start cap
                    faces.append([0, 1, 3, 2])
                    # End cap
                    last = segs * stride
                    faces.append([last + 0, last + 2, last + 3, last + 1])

                return Mesh(vertices=vertices, faces=faces, name=self.name or "Revolve")

        # Fallback: simple cylinder
        from .mesh import create_cylinder
        try:
            return create_cylinder(radius=1.0, height=1.0, segments=segs, name=self.name or "Revolve")
        except Exception:
            from .mesh import create_cube
            return create_cube(size=1.0, name=self.name or "Revolve")


class FeatureHistory:
    """Ordered timeline of features (ExtrudeFeature, RevolveFeature, ...)."""

    def __init__(
        self,
        features: Optional[List[dict]] = None,
        name: str = "Feature History",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("hist")
        self.name = name
        self.features: List[dict] = features or []
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "features": self.features,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_history_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureHistory":
        validate_history_data(data)
        return cls(
            features=data.get("features", []),
            name=data.get("name", "Feature History"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add_extrude(self, feature: ExtrudeFeature) -> None:
        self.features.append(feature.to_dict())
        self.validate()

    def add_revolve(self, feature: RevolveFeature) -> None:
        self.features.append(feature.to_dict())
        self.validate()

    def get_extrude_features(self) -> List[ExtrudeFeature]:
        result = []
        for f in self.features:
            if f.get("type") == "extrude":
                result.append(ExtrudeFeature.from_dict(f))
        return result

    def get_revolve_features(self) -> List[RevolveFeature]:
        result = []
        for f in self.features:
            if f.get("type") == "revolve":
                result.append(RevolveFeature.from_dict(f))
        return result

    def recompute_meshes(
        self,
        sketches: Dict[str, Sketch],
        parameters: Optional[ParameterStore] = None,
    ) -> Dict[str, Mesh]:
        """Recompute solid meshes for every supported feature that has a matching sketch."""
        meshes: Dict[str, Mesh] = {}
        for feat in self.get_extrude_features():
            sketch = sketches.get(feat.sketch_id)
            if sketch is not None:
                meshes[feat.id] = feat.generate_mesh(sketch, parameters)
        for feat in self.get_revolve_features():
            sketch = sketches.get(feat.sketch_id)
            if sketch is not None:
                meshes[feat.id] = feat.generate_mesh(sketch, parameters)
        return meshes
