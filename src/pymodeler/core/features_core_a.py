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
        # Prefer the largest polygon (already sorted by area in extraction for nesting)
        poly_profs = [p for p in profiles if p["type"] == "polygon"]
        if poly_profs:
            prof = poly_profs[0]
            holes = prof.get("holes") or []
            if holes:
                return self._extrude_polygon_with_holes(prof["points"], holes, length, start)
            return self._extrude_polygon(prof["points"], length, start)
        circ = next((p for p in profiles if p["type"] == "circle"), None)
        if circ:
            return self._extrude_circle(circ["center"], circ["radius"], length, start)
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

    def _extrude_polygon_with_holes(self, outer_points, holes, dist, offset):
        """Extrude an outer polygon while subtracting nested hole profiles.

        Prefers a Boolean cut (via mesh_boolean / trimesh) when an engine is
        available. Falls back to a pure side-wall construction that includes
        outer walls + reversed inner walls so the holes are geometrically present.
        """
        outer = self._extrude_polygon(outer_points, dist, offset)
        # Try Boolean subtraction for a true solid with holes
        try:
            from .boolean import mesh_boolean
            result = outer
            for hole_pts in holes:
                tool = self._extrude_polygon(hole_pts, dist, offset)
                result = mesh_boolean(result, tool, "cut", name=self.id)
            return result
        except Exception:
            # Pure fallback: build walls for outer + each hole
            return self._extrude_walls_with_holes(outer_points, holes, dist, offset)

    def _extrude_walls_with_holes(self, outer_points, holes, dist, offset):
        """Pure-Python extrusion that includes hole walls (no external Boolean).

        Top/bottom faces are the outer polygon; hole polygons are added with
        opposite winding so simple renderers still see the cut. Side walls are
        generated for the outer boundary and every hole.
        """
        verts = []
        faces = []
        # Outer bottom + top
        n = len(outer_points)
        for x, y in outer_points:
            verts.append([x, y, offset])
        for x, y in outer_points:
            verts.append([x, y, offset + dist])
        # Bottom face
        faces.append(list(range(n)))
        # Top face reversed
        faces.append(list(range(n, 2 * n))[::-1])
        # Outer sides
        for i in range(n):
            j = (i + 1) % n
            faces.append([i, j, j + n, i + n])

        # Holes
        for hole in holes:
            hn = len(hole)
            base = len(verts)
            for x, y in hole:
                verts.append([x, y, offset])
            for x, y in hole:
                verts.append([x, y, offset + dist])
            # Bottom hole face (opposite winding so it "cuts")
            faces.append(list(range(base + hn - 1, base - 1, -1)))
            # Top hole face
            faces.append(list(range(base + hn, base + 2 * hn)))
            # Inner sides (winding so normals point into the hole)
            for i in range(hn):
                j = (i + 1) % hn
                faces.append([base + i, base + i + hn, base + j + hn, base + j])

        return Mesh(vertices=verts, faces=faces, name=self.id)
