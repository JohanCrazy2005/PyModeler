"""Parametric features (Extrude, later Revolve, etc.) and feature history.

ExtrudeFeature turns a Sketch into a solid mesh driven by a numeric distance
or a ParameterStore reference. FeatureHistory is a serializable timeline.
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
_HISTORY_SCHEMA_PATH = _SCHEMA_DIR / "feature_history.schema.json"

with open(_EXTRUDE_SCHEMA_PATH, encoding="utf-8") as f:
    EXTRUDE_SCHEMA = json.load(f)
with open(_HISTORY_SCHEMA_PATH, encoding="utf-8") as f:
    HISTORY_SCHEMA = json.load(f)

_EXTRUDE_VALIDATOR = Draft202012Validator(EXTRUDE_SCHEMA)
_HISTORY_VALIDATOR = Draft202012Validator(HISTORY_SCHEMA)


class FeatureValidationError(ValueError):
    """Raised when feature or history data fails schema validation."""


def validate_extrude_data(data: dict) -> None:
    errors = sorted(_EXTRUDE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Extrude schema validation failed:\n" + "\n".join(messages))


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


class FeatureHistory:
    """Ordered timeline of features (currently ExtrudeFeature)."""

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

    def get_extrude_features(self) -> List[ExtrudeFeature]:
        result = []
        for f in self.features:
            if f.get("type") == "extrude":
                result.append(ExtrudeFeature.from_dict(f))
        return result

    def recompute_meshes(
        self,
        sketches: Dict[str, Sketch],
        parameters: Optional[ParameterStore] = None,
    ) -> Dict[str, Mesh]:
        """Recompute solid meshes for every extrude feature that has a matching sketch."""
        meshes: Dict[str, Mesh] = {}
        for feat in self.get_extrude_features():
            sketch = sketches.get(feat.sketch_id)
            if sketch is not None:
                meshes[feat.id] = feat.generate_mesh(sketch, parameters)
        return meshes
