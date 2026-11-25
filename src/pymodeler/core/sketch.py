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

    def add_diameter_dimension(self, circle_or_arc_id: str, value: float | str) -> str:
        return self.add_dimension("diameter", [circle_or_arc_id], value)

    def add_angle_dimension(self, line_a: str, line_b: str, value: float | str) -> str:
        return self.add_dimension("angle", [line_a, line_b], value)

    # --- Query helpers ---

    def update_point(self, eid: str, x: float, y: float) -> None:
        """Update the coordinates of a point entity and re-validate."""
        ent = self.get_entity(eid)
        if ent is None or ent.get("type") != "point":
            raise ValueError(f"No point entity with id {eid}")
        ent["x"] = float(x)
        ent["y"] = float(y)
        self.validate()

    def get_entity(self, eid: str) -> Optional[dict]:
        for ent in self.entities:
            if ent["id"] == eid:
                return ent
        return None

    def entity_ids_by_type(self, etype: str) -> List[str]:
        return [e["id"] for e in self.entities if e["type"] == etype]

    def solve(self, max_nfev: int = 200, tol: float = 1e-8, parameters: Optional[Any] = None) -> Dict[str, object]:
        """Solve basic geometric constraints in-place using the lightweight solver stub.

        Optional `parameters` (ParameterStore) resolves string dimension values.
        Returns the result dict from constraint_solver.solve_sketch.
        """
        from .constraint_solver import solve_sketch
        return solve_sketch(self, max_nfev=max_nfev, tol=tol, parameters=parameters)


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
    - {"type": "polygon", "points": [(x, y), ...], "holes": [[(x, y), ...], ...]}
    - {"type": "circle", "center": (x, y), "radius": float}

    Supports connected lines, circles, arcs joined into cycles when endpoints match points,
    and nested outer+holes via point-in-polygon containment.
    """
    import math

    profiles: list[dict] = []

    point_map: dict[str, tuple[float, float]] = {}
    for e in sketch.entities:
        if e["type"] == "point":
            point_map[e["id"]] = (float(e["x"]), float(e["y"]))

    def nearest_point(x: float, y: float, tol: float = 1e-4) -> str | None:
        best = None
        best_d = tol
        for pid, (px, py) in point_map.items():
            d = math.hypot(px - x, py - y)
            if d < best_d:
                best_d = d
                best = pid
        return best

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

    # Graph for cycle finding: point -> list of neighbor points
    # Also store arc intermediates: (a, b) -> intermediates from a to b
    graph: dict[str, list[str]] = {}
    arc_inter: dict[tuple[str, str], list[tuple[float, float]]] = {}

    # Lines
    for ln in [e for e in sketch.entities if e["type"] == "line" and not e.get("construction", False)]:
        a, b = ln["start_point"], ln["end_point"]
        if a in point_map and b in point_map:
            graph.setdefault(a, []).append(b)
            graph.setdefault(b, []).append(a)

    # Arcs
    for e in sketch.entities:
        if e["type"] == "arc" and not e.get("construction", False):
            cid = e["center"]
            if cid not in point_map:
                continue
            cx, cy = point_map[cid]
            r = float(e["radius"])
            sa = float(e["start_angle"])
            ea = float(e["end_angle"])
            da = (ea - sa) % 360.0
            if da < 1e-3:
                da = 360.0
            if abs(da - 360.0) < 5.0:
                profiles.append({"type": "circle", "center": (cx, cy), "radius": r})
                continue
            n = max(4, int(da / 15))
            pts = [(cx + r * math.cos(math.radians(sa + da * i / n)),
                    cy + r * math.sin(math.radians(sa + da * i / n))) for i in range(n + 1)]
            start_pt = nearest_point(pts[0][0], pts[0][1])
            end_pt = nearest_point(pts[-1][0], pts[-1][1])
            if start_pt and end_pt and start_pt != end_pt:
                inter = pts[1:-1]
                graph.setdefault(start_pt, []).append(end_pt)
                graph.setdefault(end_pt, []).append(start_pt)
                arc_inter[(start_pt, end_pt)] = inter
                arc_inter[(end_pt, start_pt)] = inter[::-1]

    # Simple cycle finder (DFS, limited)
    found_polys = []
    if graph:
        visited_edges = set()
        def ek(u, v):
            return (min(u, v), max(u, v))

        for start in list(graph):
            stack = [(start, [start], set())]
            while stack:
                node, path, used = stack.pop()
                if len(path) > 12:
                    continue
                for neigh in graph.get(node, []):
                    key = ek(node, neigh)
                    if key in used or key in visited_edges:
                        continue
                    if neigh == path[0] and len(path) >= 3:
                        # cycle of point ids
                        cycle_ids = path[:]
                        # build points, inserting arc inters
                        poly_pts = []
                        for i, pid in enumerate(cycle_ids):
                            poly_pts.append(point_map[pid])
                            nxt = cycle_ids[(i + 1) % len(cycle_ids)]
                            if (pid, nxt) in arc_inter:
                                poly_pts.extend(arc_inter[(pid, nxt)])
                        # drop closing duplicate if present
                        if len(poly_pts) > 1 and math.hypot(poly_pts[0][0]-poly_pts[-1][0], poly_pts[0][1]-poly_pts[-1][1]) < 1e-6:
                            poly_pts = poly_pts[:-1]
                        if _polygon_area(poly_pts) > 1e-8:
                            found_polys.append(poly_pts)
                        for i in range(len(cycle_ids)):
                            visited_edges.add(ek(cycle_ids[i], cycle_ids[(i+1)%len(cycle_ids)]))
                        continue
                    if neigh not in path:
                        stack.append((neigh, path + [neigh], used | {key}))

    for pts in found_polys:
        profiles.append({"type": "polygon", "points": pts})

    # Nesting
    polys = [p for p in profiles if p["type"] == "polygon"]
    if len(polys) > 1:
        polys.sort(key=lambda pp: _polygon_area(pp["points"]), reverse=True)
        for i, outer in enumerate(polys):
            outer.setdefault("holes", [])
            for inner in polys[i+1:]:
                if "parent" in inner:
                    continue
                # use centroid of inner
                icx = sum(pt[0] for pt in inner["points"]) / max(1, len(inner["points"]))
                icy = sum(pt[1] for pt in inner["points"]) / max(1, len(inner["points"]))
                if _point_in_polygon(icx, icy, outer["points"]):
                    outer["holes"].append(inner["points"])
                    inner["parent"] = True
        profiles = [p for p in profiles if p["type"] != "polygon" or "parent" not in p]
        for p in profiles:
            p.pop("parent", None)

    return profiles


def _point_in_polygon(x: float, y: float, points: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon. True if inside (boundary treated as inside)."""
    n = len(points)
    if n < 3:
        return False
    inside = False
    p1x, p1y = points[0]
    for i in range(1, n + 1):
        p2x, p2y = points[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


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
