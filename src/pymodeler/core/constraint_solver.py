"""Lightweight 2D geometric constraint solver stub.

Uses scipy.optimize.least_squares to satisfy basic geometric constraints
by adjusting free point coordinates. Fixed points and points locked by
"fixed" constraints are held constant.

Supported constraints (matching sketch schema):
- horizontal, vertical, equal (lengths), coincident, parallel, perpendicular, fixed

Not a full production solver (no radii/angles/tangent/dimensions as hard constraints yet).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

import numpy as np

try:
    from scipy.optimize import least_squares
except ImportError:  # pragma: no cover
    least_squares = None  # type: ignore


def _point_xy(ent: dict) -> Tuple[float, float]:
    return float(ent.get("x", 0.0)), float(ent.get("y", 0.0))


def _line_ends(sketch, line_id: str) -> Optional[Tuple[str, str]]:
    ent = sketch.get_entity(line_id)
    if not ent or ent.get("type") != "line":
        return None
    return ent.get("start_point"), ent.get("end_point")


def solve_sketch(sketch, max_nfev: int = 200, tol: float = 1e-8) -> Dict[str, object]:
    """Solve basic geometric constraints on a Sketch in-place.

    Returns a result dict:
        {
            "success": bool,
            "cost": float,          # final residual norm
            "nfev": int,
            "message": str,
        }
    """
    if least_squares is None:
        return {"success": False, "cost": float("inf"), "nfev": 0, "message": "scipy not available"}

    # Collect free points (not fixed flag and not subject of a fixed constraint)
    locked: Set[str] = set()
    for ent in sketch.entities:
        if ent.get("type") == "point" and ent.get("fixed", False):
            locked.add(ent["id"])
    for con in sketch.constraints:
        if con.get("type") == "fixed":
            for eid in con.get("entities", []):
                e = sketch.get_entity(eid)
                if e and e.get("type") == "point":
                    locked.add(eid)

    free_points: List[str] = []
    for ent in sketch.entities:
        if ent.get("type") == "point" and ent["id"] not in locked:
            free_points.append(ent["id"])

    if not free_points:
        return {"success": True, "cost": 0.0, "nfev": 0, "message": "no free points"}

    # Index map: point_id -> (ix, iy) in the free variable vector
    idx: Dict[str, Tuple[int, int]] = {}
    x0_list: List[float] = []
    for i, pid in enumerate(free_points):
        ent = sketch.get_entity(pid)
        x, y = _point_xy(ent)
        idx[pid] = (2 * i, 2 * i + 1)
        x0_list.extend([x, y])
    x0 = np.asarray(x0_list, dtype=float)

    def residual(x: np.ndarray) -> np.ndarray:
        # Build current coordinate map
        coords: Dict[str, Tuple[float, float]] = {}
        for pid, (ix, iy) in idx.items():
            coords[pid] = (float(x[ix]), float(x[iy]))
        for ent in sketch.entities:
            if ent.get("type") == "point" and ent["id"] not in idx:
                coords[ent["id"]] = _point_xy(ent)

        res: List[float] = []

        for con in sketch.constraints:
            ctype = con.get("type")
            ents = con.get("entities", [])

            if ctype == "horizontal" and len(ents) >= 1:
                ends = _line_ends(sketch, ents[0])
                if ends and ends[0] in coords and ends[1] in coords:
                    _, y1 = coords[ends[0]]
                    _, y2 = coords[ends[1]]
                    res.append(y2 - y1)

            elif ctype == "vertical" and len(ents) >= 1:
                ends = _line_ends(sketch, ents[0])
                if ends and ends[0] in coords and ends[1] in coords:
                    x1, _ = coords[ends[0]]
                    x2, _ = coords[ends[1]]
                    res.append(x2 - x1)

            elif ctype == "coincident" and len(ents) >= 2:
                a, b = ents[0], ents[1]
                if a in coords and b in coords:
                    ax, ay = coords[a]
                    bx, by = coords[b]
                    res.append(bx - ax)
                    res.append(by - ay)

            elif ctype == "equal" and len(ents) >= 2:
                # equal lengths of two lines
                e1, e2 = ents[0], ents[1]
                ends1 = _line_ends(sketch, e1)
                ends2 = _line_ends(sketch, e2)
                if ends1 and ends2 and all(p in coords for p in ends1 + ends2):
                    def length(ends):
                        x1, y1 = coords[ends[0]]
                        x2, y2 = coords[ends[1]]
                        return np.hypot(x2 - x1, y2 - y1)
                    res.append(length(ends1) - length(ends2))

            elif ctype in ("parallel", "perpendicular") and len(ents) >= 2:
                ends1 = _line_ends(sketch, ents[0])
                ends2 = _line_ends(sketch, ents[1])
                if ends1 and ends2 and all(p in coords for p in ends1 + ends2):
                    x1a, y1a = coords[ends1[0]]
                    x1b, y1b = coords[ends1[1]]
                    x2a, y2a = coords[ends2[0]]
                    x2b, y2b = coords[ends2[1]]
                    dx1, dy1 = x1b - x1a, y1b - y1a
                    dx2, dy2 = x2b - x2a, y2b - y2a
                    if ctype == "parallel":
                        res.append(dx1 * dy2 - dy1 * dx2)  # cross product
                    else:  # perpendicular
                        res.append(dx1 * dx2 + dy1 * dy2)  # dot product

            # fixed already handled by removing variables; ignore others for now

        return np.asarray(res, dtype=float) if res else np.zeros(1)

    if residual(x0).size == 0 or np.allclose(residual(x0), 0.0, atol=tol):
        return {"success": True, "cost": 0.0, "nfev": 0, "message": "already satisfied"}

    result = least_squares(residual, x0, ftol=tol, xtol=tol, gtol=tol, max_nfev=max_nfev)

    # Write back
    for pid, (ix, iy) in idx.items():
        ent = sketch.get_entity(pid)
        if ent is not None:
            ent["x"] = float(result.x[ix])
            ent["y"] = float(result.x[iy])

    sketch.validate()

    return {
        "success": bool(result.success),
        "cost": float(result.cost),
        "nfev": int(result.nfev),
        "message": str(result.message),
    }
