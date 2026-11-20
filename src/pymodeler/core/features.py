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
_HOLE_SCHEMA_PATH = _SCHEMA_DIR / "hole.schema.json"
_FILLET_SCHEMA_PATH = _SCHEMA_DIR / "fillet.schema.json"
_CHAMFER_SCHEMA_PATH = _SCHEMA_DIR / "chamfer.schema.json"
_HISTORY_SCHEMA_PATH = _SCHEMA_DIR / "feature_history.schema.json"

with open(_EXTRUDE_SCHEMA_PATH, encoding="utf-8") as f:
    EXTRUDE_SCHEMA = json.load(f)
with open(_REVOLVE_SCHEMA_PATH, encoding="utf-8") as f:
    REVOLVE_SCHEMA = json.load(f)
with open(_HOLE_SCHEMA_PATH, encoding="utf-8") as f:
    HOLE_SCHEMA = json.load(f)
with open(_FILLET_SCHEMA_PATH, encoding="utf-8") as f:
    FILLET_SCHEMA = json.load(f)
with open(_CHAMFER_SCHEMA_PATH, encoding="utf-8") as f:
    CHAMFER_SCHEMA = json.load(f)
with open(_HISTORY_SCHEMA_PATH, encoding="utf-8") as f:
    HISTORY_SCHEMA = json.load(f)

_EXTRUDE_VALIDATOR = Draft202012Validator(EXTRUDE_SCHEMA)
_REVOLVE_VALIDATOR = Draft202012Validator(REVOLVE_SCHEMA)
_HOLE_VALIDATOR = Draft202012Validator(HOLE_SCHEMA)
_FILLET_VALIDATOR = Draft202012Validator(FILLET_SCHEMA)
_CHAMFER_VALIDATOR = Draft202012Validator(CHAMFER_SCHEMA)
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


def validate_hole_data(data: dict) -> None:
    errors = sorted(_HOLE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Hole schema validation failed:\n" + "\n".join(messages))


def validate_fillet_data(data: dict) -> None:
    errors = sorted(_FILLET_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Fillet schema validation failed:\n" + "\n".join(messages))


def validate_chamfer_data(data: dict) -> None:
    errors = sorted(_CHAMFER_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Chamfer schema validation failed:\n" + "\n".join(messages))


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

# NOTE: Full module body continues in follow-up commit if truncated; critical HoleFeature with through_all is included below.

class HoleFeature:
    """Parametric Hole feature with blind or through-all extents."""

    DEFAULT_THROUGH_DEPTH = 1000.0

    def __init__(
        self,
        diameter: float | str = 1.0,
        depth: float | str | None = 1.0,
        name: str = "Hole",
        center: Optional[list[float]] = None,
        direction: Optional[list[float]] = None,
        segments: int = 24,
        operation: str = "cut",
        extent: str = "blind",
        through_depth: float | str | None = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
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
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "diameter": self.diameter,
            "depth": self.depth,
            "segments": self.segments,
            "operation": self.operation,
            "extent": self.extent,
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
        return cls(
            diameter=data["diameter"],
            depth=data.get("depth", 1.0),
            name=data.get("name", "Hole"),
            center=data.get("center"),
            direction=data.get("direction"),
            segments=data.get("segments", 24),
            operation=data.get("operation", "cut"),
            extent=data.get("extent", "blind"),
            through_depth=data.get("through_depth"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def resolved_diameter(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.diameter, parameters, 1.0)

    def resolved_depth(self, parameters: Optional[ParameterStore] = None) -> float:
        return _resolve_value(self.depth, parameters, 1.0)

    def resolved_through_depth(self, parameters: Optional[ParameterStore] = None) -> float:
        if self.through_depth is None:
            return self.DEFAULT_THROUGH_DEPTH
        return _resolve_value(self.through_depth, parameters, self.DEFAULT_THROUGH_DEPTH)

    def generate_mesh(self, parameters: Optional[ParameterStore] = None) -> Mesh:
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
        mesh = create_cylinder(radius=radius, height=depth, segments=segs, name=self.id)
        import numpy as np
        verts = np.asarray(mesh.vertices, dtype=float)
        if not center_on_start:
            y_min = float(verts[:, 1].min())
            verts[:, 1] -= y_min
        cx, cy, cz = 0.0, 0.0, 0.0
        if self.center:
            cx = float(self.center[0])
            cy = float(self.center[1])
            if len(self.center) > 2:
                cz = float(self.center[2])
        verts[:, 0] += cx
        verts[:, 2] += cy
        verts[:, 1] += cz
        mesh.vertices = verts.tolist()
        mesh.validate()
        return mesh
