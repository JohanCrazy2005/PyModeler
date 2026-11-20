"""Core feature validators + ExtrudeFeature."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import Any, Optional
from jsonschema import Draft202012Validator
from .mesh import Mesh
from .parameters import ParameterStore
from .sketch import Sketch, extract_simple_profiles

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
def _load(name):
    with open(_SCHEMA_DIR / name, encoding="utf-8") as f:
        return json.load(f)
EXTRUDE_SCHEMA = _load("extrude.schema.json")
REVOLVE_SCHEMA = _load("revolve.schema.json")
HOLE_SCHEMA = _load("hole.schema.json")
FILLET_SCHEMA = _load("fillet.schema.json")
CHAMFER_SCHEMA = _load("chamfer.schema.json")
HISTORY_SCHEMA = _load("feature_history.schema.json")
_EXTRUDE_VALIDATOR = Draft202012Validator(EXTRUDE_SCHEMA)
_REVOLVE_VALIDATOR = Draft202012Validator(REVOLVE_SCHEMA)
_HOLE_VALIDATOR = Draft202012Validator(HOLE_SCHEMA)
_FILLET_VALIDATOR = Draft202012Validator(FILLET_SCHEMA)
_CHAMFER_VALIDATOR = Draft202012Validator(CHAMFER_SCHEMA)
_HISTORY_VALIDATOR = Draft202012Validator(HISTORY_SCHEMA)

class FeatureValidationError(ValueError):
    pass

def _validate(validator, data, label):
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError(f"{label} schema validation failed:\n" + "\n".join(messages))

def validate_extrude_data(data: dict) -> None:
    _validate(_EXTRUDE_VALIDATOR, data, "Extrude")
def validate_revolve_data(data: dict) -> None:
    _validate(_REVOLVE_VALIDATOR, data, "Revolve")
def validate_hole_data(data: dict) -> None:
    _validate(_HOLE_VALIDATOR, data, "Hole")
def validate_fillet_data(data: dict) -> None:
    _validate(_FILLET_VALIDATOR, data, "Fillet")
def validate_chamfer_data(data: dict) -> None:
    _validate(_CHAMFER_VALIDATOR, data, "Chamfer")
def validate_history_data(data: dict) -> None:
    _validate(_HISTORY_VALIDATOR, data, "FeatureHistory")

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
    def __init__(self, sketch_id: str, distance: float | str = 1.0, name: str = "Extrude",
                 direction=None, symmetric: bool = False, start_offset: float | str = 0.0,
                 operation: str = "new", metadata=None, id: Optional[str] = None):
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
        data = {"id": self.id, "type": self.type, "name": self.name, "sketch_id": self.sketch_id,
                "distance": self.distance, "symmetric": self.symmetric, "start_offset": self.start_offset,
                "operation": self.operation}
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
        return cls(sketch_id=data["sketch_id"], distance=data["distance"], name=data.get("name", "Extrude"),
                   direction=data.get("direction"), symmetric=data.get("symmetric", False),
                   start_offset=data.get("start_offset", 0.0), operation=data.get("operation", "new"),
                   metadata=data.get("metadata"), id=data.get("id"))

    def resolved_distance(self, parameters=None) -> float:
        return _resolve_value(self.distance, parameters, 1.0)

    def resolved_start_offset(self, parameters=None) -> float:
        return _resolve_value(self.start_offset, parameters, 0.0)

    def generate_mesh(self, sketch: Sketch, parameters=None) -> Mesh:
        dist = self.resolved_distance(parameters)
        if dist <= 0:
            raise FeatureValidationError("Extrude distance must be positive")
        offset = self.resolved_start_offset(parameters)
        if self.symmetric:
            start = offset - dist / 2.0
            length = dist
        else:
            start = offset
            length = dist
        profiles = extract_simple_profiles(sketch)
        if not profiles:
            from .mesh import create_cube
            return create_cube(size=dist, name=self.id)
        prof = profiles[0]
        if prof["type"] == "polygon":
            return self._extrude_polygon(prof["points"], length, start)
        if prof["type"] == "circle":
            return self._extrude_circle(prof["center"], prof["radius"], length, start)
        from .mesh import create_cube
        return create_cube(size=1.0, name=self.id)

    def _extrude_polygon(self, points, dist, offset):
        n = len(points)
        verts = [[x, y, offset] for x, y in points] + [[x, y, offset + dist] for x, y in points]
        faces = [list(range(n)), list(range(n, 2 * n))[::-1]]
        for i in range(n):
            j = (i + 1) % n
            faces.append([i, j, j + n, i + n])
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
        verts.append([cx, cy, offset])
        verts.append([cx, cy, offset + dist])
        faces = []
        for i in range(segs):
            faces.append([i, (i + 1) % segs, segs * 2])
            faces.append([segs + i, segs * 2 + 1, segs + (i + 1) % segs])
            faces.append([i, (i + 1) % segs, segs + (i + 1) % segs, segs + i])
        return Mesh(vertices=verts, faces=faces, name=self.id)
