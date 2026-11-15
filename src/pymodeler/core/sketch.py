"""Parametric 2D Sketch data model with JSON Schema validation.

Supports entities (point, line, circle, arc), geometric constraints, and dimensions.
Designed as the foundation for history-based parametric CAD.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import jsonschema
from jsonschema import Draft202012Validator

# Resolve schema path relative to this file
_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_SKETCH_SCHEMA_PATH = _SCHEMA_DIR / "sketch.schema.json"

with open(_SKETCH_SCHEMA_PATH, encoding="utf-8") as f:
    SKETCH_SCHEMA = json.load(f)

_SKETCH_VALIDATOR = Draft202012Validator(SKETCH_SCHEMA)


class SketchValidationError(ValueError):
    """Raised when sketch data fails schema validation."""


def validate_sketch_data(data: dict) -> None:
    """Validate a dict against the Sketch JSON Schema. Raises SketchValidationError on failure."""
    errors = sorted(_SKETCH_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise SketchValidationError("Sketch schema validation failed:\n" + "\n".join(messages))


def _new_id(prefix: str = "ent") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Sketch:
    """In-memory parametric sketch that stays schema-compliant."""

    def __init__(
        self,
        name: str = "Sketch",
        plane: Optional[dict] = None,
        entities: Optional[List[dict]] = None,
        constraints: Optional[List[dict]] = None,
        dimensions: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("sketch")
        self.name = name
        self.plane = plane or {
            "origin": [0.0, 0.0, 0.0],
            "x_axis": [1.0, 0.0, 0.0],
            "y_axis": [0.0, 1.0, 0.0],
        }
        self.entities: List[dict] = entities or []
        self.constraints: List[dict] = constraints or []
        self.dimensions: List[dict] = dimensions or []
        self.metadata = metadata or {}

        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "plane": self.plane,
            "entities": self.entities,
            "constraints": self.constraints,
            "dimensions": self.dimensions,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_sketch_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Sketch":
        validate_sketch_data(data)
        return cls(
            name=data.get("name", "Sketch"),
            plane=data.get("plane"),
            entities=data.get("entities", []),
            constraints=data.get("constraints", []),
            dimensions=data.get("dimensions", []),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def __repr__(self) -> str:
        return (
            f"<Sketch id={self.id!r} name={self.name!r} "
            f"entities={len(self.entities)} constraints={len(self.constraints)} "
            f"dimensions={len(self.dimensions)}>"
        )

    # --- Entity helpers ---

    def add_point(self, x: float, y: float, construction: bool = False, fixed: bool = False) -> str:
        eid = _new_id("pt")
        self.entities.append({
            "id": eid,
            "type": "point",
            "x": float(x),
            "y": float(y),
            "construction": construction,
            "fixed": fixed,
        })
        self.validate()
        return eid

    def add_line(self, start_point: str, end_point: str, construction: bool = False) -> str:
        eid = _new_id("ln")
        self.entities.append({
            "id": eid,
            "type": "line",
            "start_point": start_point,
            "end_point": end_point,
            "construction": construction,
        })
        self.validate()
        return eid

    def add_circle(self, center: str, radius: float, construction: bool = False) -> str:
        eid = _new_id("circ")
        self.entities.append({
            "id": eid,
            "type": "circle",
            "center": center,
            "radius": float(radius),
            "construction": construction,
        })
        self.validate()
        return eid

    def add_arc(
        self,
        center: str,
        radius: float,
        start_angle: float,
        end_angle: float,
        construction: bool = False,
    ) -> str:
        eid = _new_id("arc")
        self.entities.append({
            "id": eid,
            "type": "arc",
            "center": center,
            "radius": float(radius),
            "start_angle": float(start_angle),
            "end_angle": float(end_angle),
            "construction": construction,
        })
        self.validate()
        return eid

    # --- Constraint helpers ---

    def add_constraint(self, ctype: str, entities: Sequence[str], parameters: Optional[dict] = None) -> str:
        cid = _new_id("con")
        self.constraints.append({
            "id": cid,
            "type": ctype,
            "entities": list(entities),
            "parameters": parameters or {},
        })
        self.validate()
        return cid

    def add_horizontal(self, line_id: str) -> str:
        return self.add_constraint("horizontal", [line_id])

    def add_vertical(self, line_id: str) -> str:
        return self.add_constraint("vertical", [line_id])

    def add_coincident(self, entity_a: str, entity_b: str) -> str:
        return self.add_constraint("coincident", [entity_a, entity_b])

    def add_parallel(self, line_a: str, line_b: str) -> str:
        return self.add_constraint("parallel", [line_a, line_b])

    def add_perpendicular(self, line_a: str, line_b: str) -> str:
        return self.add_constraint("perpendicular", [line_a, line_b])

    def add_equal(self, entity_a: str, entity_b: str) -> str:
        return self.add_constraint("equal", [entity_a, entity_b])

    def add_tangent(self, entity_a: str, entity_b: str) -> str:
        return self.add_constraint("tangent", [entity_a, entity_b])

    # --- Dimension helpers ---

    def add_dimension(
        self,
        dtype: str,
        entities: Sequence[str],
        value: float | str,
        driven: bool = False,
        parameters: Optional[dict] = None,
    ) -> str:
        did = _new_id("dim")
        self.dimensions.append({
            "id": did,
            "type": dtype,
            "entities": list(entities),
            "value": value,
            "driven": driven,
            "parameters": parameters or {},
        })
        self.validate()
        return did

    def add_length_dimension(self, line_id: str, value: float | str) -> str:
        return self.add_dimension("length", [line_id], value)

    def add_distance_dimension(self, entity_a: str, entity_b: str, value: float | str) -> str:
        return self.add_dimension("distance", [entity_a, entity_b], value)

    def add_radius_dimension(self, circle_or_arc_id: str, value: float | str) -> str:
        return self.add_dimension("radius", [circle_or_arc_id], value)

    # --- Query helpers ---

    def get_entity(self, eid: str) -> Optional[dict]:
        for ent in self.entities:
            if ent["id"] == eid:
                return ent
        return None

    def entity_ids_by_type(self, etype: str) -> List[str]:
        return [e["id"] for e in self.entities if e["type"] == etype]


def create_rectangle_sketch(
    width: float = 10.0,
    height: float = 5.0,
    name: str = "Rectangle",
    origin: Sequence[float] = (0.0, 0.0),
) -> Sketch:
    """Create a simple constrained rectangle sketch centered or offset from origin.

    Creates four corner points and four lines, with horizontal/vertical constraints
    and length dimensions.
    """
    sketch = Sketch(name=name)
    ox, oy = float(origin[0]), float(origin[1])

    # Corner points
    p_bl = sketch.add_point(ox, oy)
    p_br = sketch.add_point(ox + width, oy)
    p_tr = sketch.add_point(ox + width, oy + height)
    p_tl = sketch.add_point(ox, oy + height)

    # Lines
    bottom = sketch.add_line(p_bl, p_br)
    right = sketch.add_line(p_br, p_tr)
    top = sketch.add_line(p_tr, p_tl)
    left = sketch.add_line(p_tl, p_bl)

    # Constraints
    sketch.add_horizontal(bottom)
    sketch.add_horizontal(top)
    sketch.add_vertical(left)
    sketch.add_vertical(right)
    sketch.add_equal(bottom, top)
    sketch.add_equal(left, right)

    # Dimensions (parameter-ready)
    sketch.add_length_dimension(bottom, width)
    sketch.add_length_dimension(left, height)

    return sketch


def extract_simple_profiles(sketch: "Sketch") -> list[dict]:
    """Extract simple closed profiles from a sketch for feature generation.

    Returns a list of profile dicts:
    - {"type": "polygon", "points": [(x, y), ...]}  # closed, ordered
    - {"type": "circle", "center": (x, y), "radius": float}

    Currently supports:
    - Connected line entities forming a simple closed polygon (no holes)
    - Standalone circle entities
    - Arcs are discretized and can participate in polygons if connected via points

    This is a pragmatic mesh-oriented helper, not a full region finder.
    """
    import math

    profiles: list[dict] = []

    # Map point id -> (x, y)
    point_map: dict[str, tuple[float, float]] = {}
    for e in sketch.entities:
        if e["type"] == "point":
            point_map[e["id"]] = (float(e["x"]), float(e["y"]))

    # Circles
    for e in sketch.entities:
        if e["type"] == "circle" and not e.get("construction", False):
            cid = e["center"]
            if cid in point_map:
                cx, cy = point_map[cid]
                profiles.append({
                    "type": "circle",
                    "center": (cx, cy),
                    "radius": float(e["radius"]),
                })

    # Lines: build adjacency for polygon extraction
    lines = [e for e in sketch.entities if e["type"] == "line" and not e.get("construction", False)]
    if lines:
        # Graph: point_id -> list of (other_point_id, line_id)
        graph: dict[str, list[tuple[str, str]]] = {}
        for ln in lines:
            a, b = ln["start_point"], ln["end_point"]
            if a in point_map and b in point_map:
                graph.setdefault(a, []).append((b, ln["id"]))
                graph.setdefault(b, []).append((a, ln["id"]))

        # Find simple cycles (limited search for small sketches)
        visited_edges: set[tuple[str, str]] = set()

        def edge_key(u: str, v: str) -> tuple[str, str]:
            return (min(u, v), max(u, v))

        for start in list(graph.keys()):
            # DFS for cycles starting from each node, limited depth
            stack = [(start, [start], set())]  # node, path, used_edges
            while stack:
                node, path, used = stack.pop()
                if len(path) > 12:  # safety
                    continue
                for neigh, _lid in graph.get(node, []):
                    ek = edge_key(node, neigh)
                    if ek in used or ek in visited_edges:
                        continue
                    if neigh == path[0] and len(path) >= 3:
                        # Found a cycle
                        poly = [point_map[pid] for pid in path]
                        # Ensure closed and simple (area > 0)
                        if _polygon_area(poly) > 1e-8:
                            profiles.append({"type": "polygon", "points": poly})
                        visited_edges.update(edge_key(path[i], path[(i + 1) % len(path)]) for i in range(len(path)))
                        continue
                    if neigh not in path:
                        new_used = used | {ek}
                        stack.append((neigh, path + [neigh], new_used))

    # Discretize arcs and try to include them as additional polygon candidates if they form closed shapes
    # (basic: if an arc is almost full circle, treat as circle)
    for e in sketch.entities:
        if e["type"] == "arc" and not e.get("construction", False):
            cid = e["center"]
            if cid in point_map:
                cx, cy = point_map[cid]
                r = float(e["radius"])
                sa = float(e["start_angle"])
                ea = float(e["end_angle"])
                # Normalize angles
                da = (ea - sa) % 360.0
                if da < 1e-3:
                    da = 360.0
                if abs(da - 360.0) < 5.0:  # nearly full circle
                    profiles.append({
                        "type": "circle",
                        "center": (cx, cy),
                        "radius": r,
                    })
                else:
                    # Discretize into polyline points for potential use
                    n = max(4, int(da / 15))  # ~15 deg steps
                    pts = []
                    for i in range(n + 1):
                        ang = math.radians(sa + (da * i / n))
                        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
                    # Store as open for now; full loop joining is future work
                    # If start and end are close, close it
                    if math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-4:
                        profiles.append({"type": "polygon", "points": pts[:-1]})

    return profiles


def _polygon_area(points: list[tuple[float, float]]) -> float:
    """Shoelace formula. Positive for counter-clockwise."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0
