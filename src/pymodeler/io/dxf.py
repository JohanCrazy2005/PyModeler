"""DXF import/export for sketches and profiles.

Supports LINE, CIRCLE, ARC, LWPOLYLINE/POLYLINE (bulge-aware via virtual_entities),
SPLINE/ELLIPSE approximation, TEXT stub, and DIMENSION export/import with
improved entity matching and angular recovery (2-line + 3-point stub).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Optional, Sequence

import ezdxf
from ezdxf.enums import TextEntityAlignment

from pymodeler.core.sketch import Sketch, extract_simple_profiles


def _point_to_segment_dist(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """True point-to-segment distance (used for better DIMENSION entity matching)."""
    dx, dy = x2 - x1, y2 - y1
    len2 = dx * dx + dy * dy
    if len2 < 1e-12:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _nearest_entity(
    sketch: Sketch,
    x: float,
    y: float,
    etype: str,
    tol: float = 1.0,
) -> Optional[str]:
    """Find nearest entity of given type by point-to-segment or center distance."""
    best_id = None
    best_d = tol
    point_map = {e["id"]: (float(e["x"]), float(e["y"])) for e in sketch.entities if e["type"] == "point"}

    for e in sketch.entities:
        if e["type"] != etype:
            continue
        if etype == "line":
            sp = point_map.get(e.get("start_point"))
            ep = point_map.get(e.get("end_point"))
            if sp and ep:
                d = _point_to_segment_dist(x, y, sp[0], sp[1], ep[0], ep[1])
                if d < best_d:
                    best_d = d
                    best_id = e["id"]
        elif etype in ("circle", "arc"):
            c = point_map.get(e.get("center"))
            if c:
                d = math.hypot(x - c[0], y - c[1])
                if d < best_d:
                    best_d = d
                    best_id = e["id"]
        elif etype == "point":
            d = math.hypot(x - float(e["x"]), y - float(e["y"]))
            if d < best_d:
                best_d = d
                best_id = e["id"]
    return best_id


def _ensure_point(sketch: Sketch, x: float, y: float, tol: float = 0.01) -> str:
    """Return existing point id near (x,y) or create a new one."""
    for e in sketch.entities:
        if e["type"] == "point" and math.hypot(e["x"] - x, e["y"] - y) < tol:
            return e["id"]
    return sketch.add_point(x, y)


def export_sketch_to_dxf(
    sketch: Sketch,
    path: str | Path,
    include_entities: bool = True,
    include_profiles: bool = True,
    include_dimensions: bool = True,
) -> Path:
    """Export a Sketch to a DXF file.

    Entities go on layer SKETCH, closed profiles on PROFILES, dimensions on DIMENSIONS.
    """
    path = Path(path)
    doc = ezdxf.new(dxfversion="R2010", setup=True)
    msp = doc.modelspace()

    # Layers
    if "SKETCH" not in doc.layers:
        doc.layers.add("SKETCH", color=7)
    if "PROFILES" not in doc.layers:
        doc.layers.add("PROFILES", color=5)
    if "DIMENSIONS" not in doc.layers:
        doc.layers.add("DIMENSIONS", color=1)

    point_map: dict[str, tuple[float, float]] = {}
    for e in sketch.entities:
        if e["type"] == "point":
            point_map[e["id"]] = (float(e["x"]), float(e["y"]))

    if include_entities:
        for e in sketch.entities:
            if e.get("construction"):
                continue
            et = e["type"]
            if et == "line":
                sp = point_map.get(e.get("start_point"))
                ep = point_map.get(e.get("end_point"))
                if sp and ep:
                    msp.add_line(sp, ep, dxfattribs={"layer": "SKETCH"})
            elif et == "circle":
                c = point_map.get(e.get("center"))
                if c:
                    msp.add_circle(c, float(e["radius"]), dxfattribs={"layer": "SKETCH"})
            elif et == "arc":
                c = point_map.get(e.get("center"))
                if c:
                    msp.add_arc(
                        c,
                        float(e["radius"]),
                        float(e.get("start_angle", 0.0)),
                        float(e.get("end_angle", 360.0)),
                        dxfattribs={"layer": "SKETCH"},
                    )

    if include_profiles:
        profiles = extract_simple_profiles(sketch)
        for p in profiles:
            if p["type"] == "polygon" and p.get("points"):
                pts = [(float(x), float(y)) for x, y in p["points"]]
                if len(pts) >= 3:
                    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "PROFILES"})
            elif p["type"] == "circle":
                cx, cy = p["center"]
                msp.add_circle((cx, cy), p["radius"], dxfattribs={"layer": "PROFILES"})

    if include_dimensions:
        _export_dimensions(sketch, msp, point_map)

    doc.saveas(path)
    return path


def _export_dimensions(sketch: Sketch, msp, point_map: dict) -> None:
    """Emit DIMENSION entities for sketch dimensions. Failures are skipped."""
    for dim in sketch.dimensions:
        dtype = dim.get("type")
        ents = dim.get("entities", [])
        try:
            value = float(dim.get("value", 0))
        except (TypeError, ValueError):
            value = 0.0
        params = dim.get("parameters") or {}

        try:
            if dtype in ("length", "distance") and ents:
                # Prefer first line
                line = next((e for e in sketch.entities if e["id"] == ents[0] and e["type"] == "line"), None)
                if line:
                    sp = point_map.get(line.get("start_point"))
                    ep = point_map.get(line.get("end_point"))
                    if sp and ep:
                        # Offset base a bit above the line
                        mid = ((sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2 + 5.0)
                        dim_ent = msp.add_linear_dim(
                            base=mid, p1=sp, p2=ep, dxfattribs={"layer": "DIMENSIONS"}
                        )
                        dim_ent.render()
            elif dtype == "aligned" and ents:
                line = next((e for e in sketch.entities if e["id"] == ents[0] and e["type"] == "line"), None)
                if line:
                    sp = point_map.get(line.get("start_point"))
                    ep = point_map.get(line.get("end_point"))
                    if sp and ep:
                        dist = float(params.get("distance", 5.0))
                        style = params.get("leader_style", "straight")
                        if style == "none":
                            dist = 0.0
                        elif style == "angled":
                            dist = dist * 1.15  # slight extra offset for angled look
                        dim_ent = msp.add_aligned_dim(
                            p1=sp, p2=ep, distance=dist, dxfattribs={"layer": "DIMENSIONS"}
                        )
                        dim_ent.render()
            elif dtype == "radius" and ents:
                circ = next((e for e in sketch.entities if e["id"] == ents[0] and e["type"] in ("circle", "arc")), None)
                if circ:
                    c = point_map.get(circ.get("center"))
                    if c:
                        r = float(circ.get("radius", value))
                        dim_ent = msp.add_radius_dim(
                            center=c, radius=r, angle=45.0, dxfattribs={"layer": "DIMENSIONS"}
                        )
                        dim_ent.render()
            elif dtype == "diameter" and ents:
                circ = next((e for e in sketch.entities if e["id"] == ents[0] and e["type"] in ("circle", "arc")), None)
                if circ:
                    c = point_map.get(circ.get("center"))
                    if c:
                        r = float(circ.get("radius", value / 2))
                        dim_ent = msp.add_diameter_dim(
                            center=c, radius=r, angle=30.0, dxfattribs={"layer": "DIMENSIONS"}
                        )
                        dim_ent.render()
            elif dtype == "angle" and len(ents) >= 2:
                l1 = next((e for e in sketch.entities if e["id"] == ents[0] and e["type"] == "line"), None)
                l2 = next((e for e in sketch.entities if e["id"] == ents[1] and e["type"] == "line"), None)
                if l1 and l2:
                    p1 = point_map.get(l1.get("start_point"))
                    p2 = point_map.get(l1.get("end_point"))
                    p3 = point_map.get(l2.get("start_point"))
                    p4 = point_map.get(l2.get("end_point"))
                    if p1 and p2 and p3 and p4:
                        # Base near the common vertex or midpoint
                        base = p1 if p1 == p3 or p1 == p4 else ((p1[0] + p3[0]) / 2, (p1[1] + p3[1]) / 2)
                        dim_ent = msp.add_angular_dim_2l(
                            base=base,
                            line1=(p1, p2),
                            line2=(p3, p4),
                            dxfattribs={"layer": "DIMENSIONS"},
                        )
                        dim_ent.render()
            elif dtype == "ordinate" and ents:
                pt = next((e for e in sketch.entities if e["id"] == ents[0] and e["type"] == "point"), None)
                if pt:
                    feat = (float(pt["x"]), float(pt["y"]))
                    origin = tuple(params.get("origin", (0.0, 0.0)))
                    offset = float(params.get("offset", 10.0))
                    axis = params.get("axis", "x")
                    style = params.get("leader_style", "straight")
                    # Respect leader_style: none → minimal leader, angled → diagonal offset
                    if style == "none":
                        ox, oy = (0.1, 0.0) if axis == "x" else (0.0, 0.1)
                    elif style == "angled":
                        ox, oy = (offset * 0.7, offset * 0.5) if axis == "x" else (offset * 0.5, offset * 0.7)
                    else:  # straight
                        ox, oy = (offset, 0.0) if axis == "x" else (0.0, offset)
                    if axis == "x":
                        dim_ent = msp.add_ordinate_x_dim(
                            feature_location=feat,
                            offset=(ox, oy),
                            origin=origin,
                            dxfattribs={"layer": "DIMENSIONS"},
                        )
                    else:
                        dim_ent = msp.add_ordinate_y_dim(
                            feature_location=feat,
                            offset=(ox, oy),
                            origin=origin,
                            dxfattribs={"layer": "DIMENSIONS"},
                        )
                    dim_ent.render()
        except Exception:
            # Skip individual dimension failures for robustness
            continue


def export_profiles_to_dxf(profiles: Sequence[dict], path: str | Path) -> Path:
    """Export a list of profile dicts (from extract_simple_profiles) to DXF."""
    path = Path(path)
    doc = ezdxf.new(dxfversion="R2010", setup=True)
    msp = doc.modelspace()
    if "PROFILES" not in doc.layers:
        doc.layers.add("PROFILES", color=5)

    for p in profiles:
        if p.get("type") == "polygon" and p.get("points"):
            pts = [(float(x), float(y)) for x, y in p["points"]]
            if len(pts) >= 3:
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "PROFILES"})
        elif p.get("type") == "circle":
            msp.add_circle(p["center"], p["radius"], dxfattribs={"layer": "PROFILES"})

    doc.saveas(path)
    return path


def import_dxf_to_sketch(
    path: str | Path,
    name: str = "Imported",
    import_dimensions: bool = True,
    approx_distance: float = 0.1,
) -> Sketch:
    """Import a DXF file into a Sketch.

    Supports LINE, CIRCLE, ARC, LWPOLYLINE/POLYLINE (bulge → ARC via virtual_entities),
    SPLINE/ELLIPSE (flattened to lines with approx_distance), TEXT (point + metadata),
    and DIMENSION recovery with improved matching.
    """
    path = Path(path)
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    sketch = Sketch(name=name)
    sketch.metadata.setdefault("imported_texts", [])

    # First pass: geometry
    for entity in msp:
        et = entity.dxftype()
        try:
            if et == "LINE":
                s = entity.dxf.start
                e = entity.dxf.end
                p1 = _ensure_point(sketch, s.x, s.y)
                p2 = _ensure_point(sketch, e.x, e.y)
                sketch.add_line(p1, p2)
            elif et == "CIRCLE":
                c = entity.dxf.center
                cid = _ensure_point(sketch, c.x, c.y)
                sketch.add_circle(cid, float(entity.dxf.radius))
            elif et == "ARC":
                c = entity.dxf.center
                cid = _ensure_point(sketch, c.x, c.y)
                sketch.add_arc(
                    cid,
                    float(entity.dxf.radius),
                    float(entity.dxf.start_angle),
                    float(entity.dxf.end_angle),
                )
            elif et in ("LWPOLYLINE", "POLYLINE"):
                # Use virtual_entities so bulges become ARC/LINE
                for ve in entity.virtual_entities():
                    vet = ve.dxftype()
                    if vet == "LINE":
                        s = ve.dxf.start
                        e = ve.dxf.end
                        p1 = _ensure_point(sketch, s.x, s.y)
                        p2 = _ensure_point(sketch, e.x, e.y)
                        sketch.add_line(p1, p2)
                    elif vet == "ARC":
                        c = ve.dxf.center
                        cid = _ensure_point(sketch, c.x, c.y)
                        sketch.add_arc(
                            cid,
                            float(ve.dxf.radius),
                            float(ve.dxf.start_angle),
                            float(ve.dxf.end_angle),
                        )
            elif et in ("SPLINE", "ELLIPSE"):
                # Approximate via flattening
                try:
                    pts = list(entity.flattening(distance=approx_distance))
                    for i in range(len(pts) - 1):
                        p1 = _ensure_point(sketch, pts[i][0], pts[i][1])
                        p2 = _ensure_point(sketch, pts[i + 1][0], pts[i + 1][1])
                        sketch.add_line(p1, p2)
                except Exception:
                    pass
            elif et == "TEXT":
                ins = entity.dxf.insert
                pid = _ensure_point(sketch, ins.x, ins.y)
                sketch.metadata["imported_texts"].append({
                    "text": getattr(entity.dxf, "text", ""),
                    "x": ins.x,
                    "y": ins.y,
                    "height": getattr(entity.dxf, "height", 1.0),
                    "rotation": getattr(entity.dxf, "rotation", 0.0),
                    "point_id": pid,
                })
        except Exception:
            continue

    if import_dimensions:
        _import_dimensions(sketch, msp)

    return sketch


def add_ordinate_group(
    sketch: Sketch,
    points: Sequence[tuple[str, float]],
    axis: str = "x",
    origin: Sequence[float] = (0.0, 0.0),
    offset: float = 12.0,
    leader_style: str = "straight",
    group_id: Optional[str] = None,
) -> list[str]:
    """Create a multi-feature ordinate set sharing the same origin.

    points: sequence of (point_id, value) pairs.
    Returns list of dimension ids. Useful for manufacturing drawings
    that need stacked ordinates from a common datum.
    Stamps a shared group_id and leader_style on each dimension.
    """
    import uuid
    gid = group_id or f"ordgrp_{uuid.uuid4().hex[:6]}"
    ids = []
    for pid, val in points:
        did = sketch.add_ordinate_dimension(
            pid, val, axis=axis, origin=origin, offset=offset,
            leader_style=leader_style, group_id=gid,
        )
        ids.append(did)
    return ids


def _import_dimensions(sketch: Sketch, msp) -> None:
    """Recover DIMENSION entities into sketch dimensions with improved matching."""
    for dim in msp.query("DIMENSION"):
        try:
            dimtype = getattr(dim, "dimtype", None)
            measurement = None
            try:
                measurement = dim.get_measurement()
            except Exception:
                measurement = None

            # Definition points
            defpoint = getattr(dim.dxf, "defpoint", None)
            defpoint2 = getattr(dim.dxf, "defpoint2", None)
            defpoint3 = getattr(dim.dxf, "defpoint3", None)
            defpoint4 = getattr(dim.dxf, "defpoint4", None)
            defpoint5 = getattr(dim.dxf, "defpoint5", None)

            # Radius / diameter (dimtype 4 / 3)
            if dimtype in (4, 3, 163):  # radius or diameter variants
                center = defpoint or defpoint2
                if center is not None:
                    cid = _nearest_entity(sketch, center.x, center.y, "circle", tol=2.0)
                    if cid is None:
                        cid = _nearest_entity(sketch, center.x, center.y, "arc", tol=2.0)
                    if cid is None:
                        # Create supporting circle if measurement available
                        r = abs(measurement) if measurement else 1.0
                        if dimtype == 3:
                            r = r / 2.0
                        pid = _ensure_point(sketch, center.x, center.y)
                        cid = sketch.add_circle(pid, r)
                    val = measurement if measurement is not None else 0.0
                    dtype = "radius" if dimtype == 4 else "diameter"
                    sketch.add_dimension(dtype, [cid], val)
                continue

            # Ordinate (dimtype 6)
            if dimtype in (6, 70):
                feat = defpoint2 or defpoint
                if feat is not None:
                    pid = _nearest_entity(sketch, feat.x, feat.y, "point", tol=1.5)
                    if pid is None:
                        pid = _ensure_point(sketch, feat.x, feat.y)
                    axis = "x" if abs(getattr(dim.dxf, "defpoint3", feat).x - feat.x) < 0.1 else "y"
                    val = measurement if measurement is not None else (feat.x if axis == "x" else feat.y)
                    sketch.add_ordinate_dimension(pid, val, axis=axis)
                continue

            # Angular 2-line (dimtype 2) or 3-point (dimtype 5)
            if dimtype in (2, 5):
                # Pair definition points to recover supporting lines
                pts = []
                for dp in (defpoint, defpoint2, defpoint3, defpoint4, defpoint5):
                    if dp is not None:
                        pts.append((dp.x, dp.y))
                if len(pts) >= 4 or dimtype == 5:
                    # Create or match two lines
                    if dimtype == 5 and len(pts) >= 3:
                        # 3-point angular: vertex + two ends
                        v = pts[0]
                        a = pts[1]
                        b = pts[2]
                        p_v = _ensure_point(sketch, v[0], v[1])
                        p_a = _ensure_point(sketch, a[0], a[1])
                        p_b = _ensure_point(sketch, b[0], b[1])
                        l1 = sketch.add_line(p_v, p_a)
                        l2 = sketch.add_line(p_v, p_b)
                        val = measurement if measurement is not None else 90.0
                        sketch.add_angle_dimension(l1, l2, val)
                    else:
                        # 2-line: try to match or create from pairs
                        # Use first two pairs
                        pairs = [(pts[0], pts[1]), (pts[2], pts[3])] if len(pts) >= 4 else []
                        line_ids = []
                        for p_a, p_b in pairs:
                            # Try match existing line by midpoint proximity
                            mid = ((p_a[0] + p_b[0]) / 2, (p_a[1] + p_b[1]) / 2)
                            lid = _nearest_entity(sketch, mid[0], mid[1], "line", tol=1.5)
                            if lid is None:
                                ida = _ensure_point(sketch, p_a[0], p_a[1])
                                idb = _ensure_point(sketch, p_b[0], p_b[1])
                                lid = sketch.add_line(ida, idb)
                            line_ids.append(lid)
                        if len(line_ids) >= 2:
                            val = measurement if measurement is not None else 90.0
                            sketch.add_angle_dimension(line_ids[0], line_ids[1], val)
                continue

            # Linear / aligned (dimtype 0 / 1)
            if dimtype in (0, 1, 32, 33) or dimtype is None:
                # Use defpoint2 / defpoint3 as the measured points
                p1 = defpoint2
                p2 = defpoint3
                if p1 is not None and p2 is not None:
                    mid = ((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
                    lid = _nearest_entity(sketch, mid[0], mid[1], "line", tol=1.5)
                    if lid is None:
                        id1 = _ensure_point(sketch, p1.x, p1.y)
                        id2 = _ensure_point(sketch, p2.x, p2.y)
                        lid = sketch.add_line(id1, id2)
                    val = measurement if measurement is not None else math.hypot(p2.x - p1.x, p2.y - p1.y)
                    dtype = "aligned" if dimtype == 1 else "length"
                    if dtype == "aligned":
                        sketch.add_aligned_dimension(lid, val)
                    else:
                        sketch.add_length_dimension(lid, val)
        except Exception:
            continue
