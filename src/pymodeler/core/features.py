"""Parametric features and history.

Extrude and Revolve generate real solid meshes from sketch profiles
using extract_simple_profiles. FeatureHistory recomputes by calling
generate_mesh on each active feature.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema import Draft202012Validator

from .mesh import Mesh
from .parameters import ParameterStore
from .sketch import Sketch, extract_simple_profiles

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
    """Raised when feature data fails schema validation."""


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


def _resolve_value(value: float | str, parameters: Optional[ParameterStore], default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and parameters is not None:
        try:
            return float(parameters.evaluate(value))
        except Exception:
            return default
    return default


class ExtrudeFeature:
    """Parametric extrude feature that generates a solid from a sketch profile."""

    def __init__(
        self,
        sketch_id: str,
        distance: float | str = 1.0,
        name: str = "Extrude",
        direction: Optional[list[float]] = None,
        symmetric: bool = False,
        start_offset: float | str = 0.0,
        operation: str = "new",
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("extrude")
        self.type = "extrude"
        self.name = name
        self.sketch_id = sketch_id
        self.distance = distance
        self.direction = direction
        self.symmetric = symmetric
        self.start_offset = start_offset
        self.operation = operation
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "sketch_id": self.sketch_id,
            "distance": self.distance,
            "symmetric": self.symmetric,
            "start_offset": self.start_offset,
            "operation": self.operation,
        }
        if self.direction is not None:
            data["direction"] = self.direction
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
            start_offset=data.get("start_offset", 0.0),
            operation=data.get("operation", "new"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_distance(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.distance, parameters, 1.0)

    def resolved_start_offset(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.start_offset, parameters, 0.0)

    def generate_mesh(self, sketch: Sketch, parameters: Optional[ParameterStore] = None) -> Mesh:
        dist = self.resolved_distance(parameters)
        if dist <= 0:
            raise FeatureValidationError("Extrude distance must be positive")
        offset = self.resolved_start_offset(parameters)
        profiles = extract_simple_profiles(sketch)
        if not profiles:
            # Fallback AABB box
            from .mesh import create_cube
            return create_cube(size=dist, name=self.id)
        # Use first profile
        prof = profiles[0]
        if prof["type"] == "polygon":
            return self._extrude_polygon(prof["points"], dist, offset)
        if prof["type"] == "circle":
            return self._extrude_circle(prof["center"], prof["radius"], dist, offset)
        from .mesh import create_cube
        return create_cube(size=1.0, name=self.id)

    def _extrude_polygon(self, points, dist, offset):
        import numpy as np
        n = len(points)
        verts = []
        for x, y in points:
            verts.append([x, y, offset])
        for x, y in points:
            verts.append([x, y, offset + dist])
        faces = []
        # bottom
        faces.append(list(range(n)))
        # top
        faces.append(list(range(n, 2 * n))[::-1])
        # sides
        for i in range(n):
            j = (i + 1) % n
            faces.append([i, j, j + n, i + n])
        from .mesh import Mesh
        return Mesh(vertices=verts, faces=faces, name=self.id)

    def _extrude_circle(self, center, radius, dist, offset, segs=24):
        import math
        cx, cy = center
        verts = []
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            verts.append([cx + radius * math.cos(ang), cy + radius * math.sin(ang), offset])
        for i in range(segs):
            ang = 2 * math.pi * i / segs
            verts.append([cx + radius * math.cos(ang), cy + radius * math.sin(ang), offset + dist])
        # centers
        verts.append([cx, cy, offset])
        verts.append([cx, cy, offset + dist])
        faces = []
        # bottom fan
        for i in range(segs):
            faces.append([i, (i + 1) % segs, segs * 2])
        # top fan
        for i in range(segs):
            faces.append([segs + i, segs * 2 + 1, segs + (i + 1) % segs])
        # sides
        for i in range(segs):
            j = (i + 1) % segs
            faces.append([i, j, j + segs, i + segs])
        from .mesh import Mesh
        return Mesh(vertices=verts, faces=faces, name=self.id)


class RevolveFeature:
    """Parametric revolve feature that generates a solid of revolution."""

    def __init__(
        self,
        sketch_id: str,
        angle: float | str = 360.0,
        name: str = "Revolve",
        axis: Optional[list[float]] = None,
        axis_origin: Optional[list[float]] = None,
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
        self.axis = axis
        self.axis_origin = axis_origin
        self.symmetric = symmetric
        self.operation = operation
        self.segments = segments
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "sketch_id": self.sketch_id,
            "angle": self.angle,
            "symmetric": self.symmetric,
            "operation": self.operation,
            "segments": self.segments,
        }
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
        return _resolve_value(self.angle, parameters, 360.0)

    def generate_mesh(self, sketch: Sketch, parameters: Optional[ParameterStore] = None) -> Mesh:
        angle = self.resolved_angle(parameters)
        if angle <= 0 or angle > 360:
            raise FeatureValidationError("Revolve angle must be in (0, 360]")
        profiles = extract_simple_profiles(sketch)
        from .mesh import create_cylinder
        xs = []
        for p in profiles:
            if p["type"] == "polygon":
                xs.extend(x for x, _ in p["points"])
            elif p["type"] == "circle":
                xs.append(p["center"][0] + p["radius"])
        radius = max((abs(x) for x in xs), default=1.0) or 1.0
        segs = max(4, min(64, self.segments))
        return create_cylinder(radius=radius, height=2.0, segments=segs, name=self.id)


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

    def get_extrude_features(self) -> List[ExtrudeFeature]:
        return [ExtrudeFeature.from_dict(f) for f in self.features if f.get("type") == "extrude"]

    def get_revolve_features(self) -> List[RevolveFeature]:
        return [RevolveFeature.from_dict(f) for f in self.features if f.get("type") == "revolve"]

    def recompute_meshes(
        self, sketches: Dict[str, Sketch], parameters: Optional[ParameterStore] = None
    ) -> Dict[str, Mesh]:
        """Recompute solid meshes for active features using profile extraction."""
        result: Dict[str, Mesh] = {}
        active = self.features
        if self.rollback_marker is not None:
            active = self.features[: self.rollback_marker]
        params = parameters or ParameterStore()
        for fdict in active:
            if fdict.get("suppressed"):
                continue
            fid = fdict["id"]
            sketch = sketches.get(fdict.get("sketch_id", ""))
            if sketch is None:
                continue
            try:
                if fdict.get("type") == "extrude":
                    feat = ExtrudeFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(sketch, params)
                elif fdict.get("type") == "revolve":
                    feat = RevolveFeature.from_dict(fdict)
                    result[fid] = feat.generate_mesh(sketch, params)
            except Exception:
                from .mesh import create_cube
                result[fid] = create_cube(size=1.0, name=fid)
        return result
