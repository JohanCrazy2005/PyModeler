"""DXF export stubs for sketches and 2D profiles using ezdxf.

Provides simple export of Sketch entities and extracted closed profiles
to DXF files suitable for 2D drawings, CNC, or manufacturing workflows.
Also supports basic DIMENSION entities driven by sketch dimensions.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, Union

try:
    import ezdxf
    from ezdxf.document import Drawing
    from ezdxf.layouts import Modelspace
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "ezdxf is required for DXF export. Install with: pip install ezdxf"
    ) from e

from pymodeler.core.sketch import Sketch, extract_simple_profiles


def export_sketch_to_dxf(
    sketch: Sketch,
    path: Union[str, Path],
    *,
    include_entities: bool = True,
    include_profiles: bool = True,
    include_dimensions: bool = True,
    profile_layer: str = "PROFILES",
    entity_layer: str = "SKETCH",
    dimension_layer: str = "DIMENSIONS",
) -> Path:
    """Export a Sketch to a DXF file.

    - Non-construction entities (lines, circles, arcs) are written to the entity layer.
    - Closed profiles extracted by ``extract_simple_profiles`` are written as
      closed LWPOLYLINEs (polygons) or CIRCLEs on the profile layer.
    - Sketch dimensions (length, radius, diameter, angle) are written as DIMENSION entities on the
      dimension layer when ``include_dimensions`` is True.

    Returns the path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc: Drawing = ezdxf.new(dxfversion="R2010", setup=True)
    msp: Modelspace = doc.modelspace()

    # Layers
    if entity_layer not in doc.layers:
        doc.layers.add(entity_layer, color=7)
    if profile_layer not in doc.layers:
        doc.layers.add(profile_layer, color=1)  # red for profiles
    if dimension_layer not in doc.layers:
        doc.layers.add(dimension_layer, color=3)  # green for dimensions

    point_map: dict[str, tuple[float, float]] = {}
    for e in sketch.entities:
        if e["type"] == "point":
            point_map[e["id"]] = (float(e["x"]), float(e["y"]))

    if include_entities:
        _add_entities(msp, sketch, point_map, entity_layer)

    if include_profiles:
        profiles = extract_simple_profiles(sketch)
        _add_profiles(msp, profiles, profile_layer)

    if include_dimensions and sketch.dimensions:
        _add_dimensions(msp, sketch, point_map, dimension_layer)

    doc.saveas(path)
    return path


def _add_entities(
    msp: Modelspace,
    sketch: Sketch,
    point_map: dict[str, tuple[float, float]],
    layer: str,
) -> None:
    for e in sketch.entities:
        if e.get("construction", False):
            continue
        etype = e["type"]
        if etype == "line":
            start = point_map.get(e["start_point"])
            end = point_map.get(e["end_point"])
            if start and end:
                msp.add_line(start, end, dxfattribs={"layer": layer})
        elif etype == "circle":
            center = point_map.get(e["center"])
            if center:
                msp.add_circle(
                    center,
                    radius=float(e["radius"]),
                    dxfattribs={"layer": layer},
                )
        elif etype == "arc":
            center = point_map.get(e["center"])
            if center:
                # ezdxf angles are in degrees, CCW from positive X
                msp.add_arc(
                    center,
                    radius=float(e["radius"]),
                    start_angle=float(e["start_angle"]),
                    end_angle=float(e["end_angle"]),
                    dxfattribs={"layer": layer},
                )
        # points are not typically exported as DXF points unless needed


def _add_profiles(msp: Modelspace, profiles: list[dict], layer: str) -> None:
    for prof in profiles:
        ptype = prof["type"]
        if ptype == "polygon":
            points = prof["points"]
            if len(points) >= 3:
                # Closed LWPOLYLINE
                msp.add_lwpolyline(
                    points,
                    close=True,
                    dxfattribs={"layer": layer},
                )
        elif ptype == "circle":
            cx, cy = prof["center"]
            msp.add_circle(
                (cx, cy),
                radius=float(prof["radius"]),
                dxfattribs={"layer": layer},
            )


def _add_dimensions(
    msp: Modelspace,
    sketch: Sketch,
    point_map: dict[str, tuple[float, float]],
    layer: str,
) -> None:
    """Add DIMENSION entities for sketch dimensions with improved placement.

    Supports:
    - length / distance on a line (linear dimension, user or value-driven offset + side)
    - radius on circle or arc (user angle or default)
    - diameter on circle or arc (user angle or default)
    - angle between two lines (2-line angular, user or value-driven offset)
    - aligned on a line (parallel dimension line, distance parameter)
    - ordinate on a point (x or y type relative to origin, offset parameter)

    Placement parameters are read from dim["parameters"]:
    - offset: float (absolute distance for the dimension line)
    - side: float (+1 or -1) for which side of the entity
    - angle: float (degrees) for radial/diameter placement
    """
    entity_by_id = {e["id"]: e for e in sketch.entities}

    for dim in sketch.dimensions:
        dtype = dim.get("type")
        ents = dim.get("entities", [])
        if not ents:
            continue
        params = dim.get("parameters") or {}
        try:
            if dtype in ("length", "distance") and len(ents) >= 1:
                # Prefer first entity if it is a line
                eid = ents[0]
                ent = entity_by_id.get(eid)
                if ent and ent["type"] == "line":
                    start = point_map.get(ent["start_point"])
                    end = point_map.get(ent["end_point"])
                    if start and end:
                        dx = end[0] - start[0]
                        dy = end[1] - start[1]
                        length = math.hypot(dx, dy) or 1.0
                        # Perp unit vector
                        px, py = -dy / length, dx / length
                        side = float(params.get("side", 1.0))
                        # Value-driven default: ~20% of measured length, min 5
                        try:
                            val = float(dim.get("value", length))
                        except (TypeError, ValueError):
                            val = length
                        default_off = max(5.0, abs(val) * 0.2)
                        offset = float(params.get("offset", default_off)) * (1.0 if side >= 0 else -1.0)
                        base = (
                            (start[0] + end[0]) / 2 + px * offset,
                            (start[1] + end[1]) / 2 + py * offset,
                        )
                        dim_ent = msp.add_linear_dim(
                            base=base,
                            p1=start,
                            p2=end,
                            dimstyle="EZDXF",
                            dxfattribs={"layer": layer},
                        )
                        dim_ent.render()
            elif dtype == "radius" and len(ents) >= 1:
                eid = ents[0]
                ent = entity_by_id.get(eid)
                if ent and ent["type"] in ("circle", "arc"):
                    center = point_map.get(ent["center"])
                    if center:
                        radius = float(ent["radius"])
                        angle = float(params.get("angle", 45.0))
                        dim_ent = msp.add_radius_dim(
                            center=center,
                            radius=radius,
                            angle=angle,
                            dimstyle="EZ_RADIUS",
                            dxfattribs={"layer": layer},
                        )
                        dim_ent.render()
            elif dtype == "diameter" and len(ents) >= 1:
                eid = ents[0]
                ent = entity_by_id.get(eid)
                if ent and ent["type"] in ("circle", "arc"):
                    center = point_map.get(ent["center"])
                    if center:
                        radius = float(ent["radius"])
                        angle = float(params.get("angle", 30.0))
                        dim_ent = msp.add_diameter_dim(
                            center=center,
                            radius=radius,
                            angle=angle,
                            dimstyle="EZ_RADIUS",
                            dxfattribs={"layer": layer},
                        )
                        dim_ent.render()
            elif dtype == "angle" and len(ents) >= 2:
                # Prefer two lines for 2-line angular dimension
                e1 = entity_by_id.get(ents[0])
                e2 = entity_by_id.get(ents[1])
                if (
                    e1 and e2
                    and e1["type"] == "line"
                    and e2["type"] == "line"
                ):
                    p1 = point_map.get(e1["start_point"])
                    p2 = point_map.get(e1["end_point"])
                    p3 = point_map.get(e2["start_point"])
                    p4 = point_map.get(e2["end_point"])
                    if p1 and p2 and p3 and p4:
                        mid1 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                        mid2 = ((p3[0] + p4[0]) / 2, (p3[1] + p4[1]) / 2)
                        # Value-driven default offset
                        try:
                            val = float(dim.get("value", 90.0))
                        except (TypeError, ValueError):
                            val = 90.0
                        default_off = max(5.0, abs(val) * 0.1)
                        offset = float(params.get("offset", default_off))
                        base = (
                            (mid1[0] + mid2[0]) / 2 + offset,
                            (mid1[1] + mid2[1]) / 2 + offset,
                        )
                        dim_ent = msp.add_angular_dim_2l(
                            base=base,
                            line1=(p1, p2),
                            line2=(p3, p4),
                            dimstyle="EZ_CURVED",
                            dxfattribs={"layer": layer},
                        )
                        dim_ent.render()
            elif dtype == "aligned" and len(ents) >= 1:
                eid = ents[0]
                ent = entity_by_id.get(eid)
                if ent and ent["type"] == "line":
                    start = point_map.get(ent["start_point"])
                    end = point_map.get(ent["end_point"])
                    if start and end:
                        distance = float(params.get("distance", params.get("offset", 5.0)))
                        dim_ent = msp.add_aligned_dim(
                            p1=start,
                            p2=end,
                            distance=distance,
                            dimstyle="EZDXF",
                            dxfattribs={"layer": layer},
                        )
                        dim_ent.render()
            elif dtype == "ordinate" and len(ents) >= 1:
                eid = ents[0]
                ent = entity_by_id.get(eid)
                if ent and ent["type"] == "point":
                    feature = point_map.get(eid)
                    if feature:
                        origin = params.get("origin", [0.0, 0.0])
                        if isinstance(origin, (list, tuple)) and len(origin) >= 2:
                            origin_pt = (float(origin[0]), float(origin[1]))
                        else:
                            origin_pt = (0.0, 0.0)
                        axis = str(params.get("axis", "x")).lower()
                        offset_val = float(params.get("offset", 10.0))
                        # offset relative to feature
                        if axis == "y":
                            offset = (offset_val, 0.0)
                            dim_ent = msp.add_ordinate_y_dim(
                                feature_location=feature,
                                offset=offset,
                                origin=origin_pt,
                                dimstyle="EZDXF",
                                dxfattribs={"layer": layer},
                            )
                        else:
                            offset = (0.0, -offset_val if feature[1] >= origin_pt[1] else offset_val)
                            dim_ent = msp.add_ordinate_x_dim(
                                feature_location=feature,
                                offset=offset,
                                origin=origin_pt,
                                dimstyle="EZDXF",
                                dxfattribs={"layer": layer},
                            )
                        dim_ent.render()
            # future: 3-point angular, etc.
        except Exception:
            # Skip dimensions that fail to render (robustness)
            continue


def export_profiles_to_dxf(
    profiles: list[dict],
    path: Union[str, Path],
    *,
    layer: str = "PROFILES",
) -> Path:
    """Export a list of profile dicts (from extract_simple_profiles) directly to DXF.

    Useful when you already have extracted polygons / circles.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = ezdxf.new(dxfversion="R2010", setup=True)
    msp = doc.modelspace()
    if layer not in doc.layers:
        doc.layers.add(layer, color=1)

    _add_profiles(msp, profiles, layer)
    doc.saveas(path)
    return path


def _import_dimensions(sketch: Sketch, msp, get_or_add_point) -> None:
    """Recover basic DIMENSION entities into sketch dimensions.

    Matches definition points to nearby existing entities (or creates points/lines)
    and uses get_measurement() for the value. Skips on any failure.
    """
    # Build simple spatial index of existing entities by points
    point_map = {e["id"]: (float(e["x"]), float(e["y"])) for e in sketch.entities if e["type"] == "point"}

    def nearest_entity(x: float, y: float, etypes: tuple, tol: float = 0.5) -> Optional[str]:
        best_id = None
        best_d = tol
        for e in sketch.entities:
            if e["type"] not in etypes:
                continue
            if e["type"] == "line":
                sp = point_map.get(e["start_point"])
                ep = point_map.get(e["end_point"])
                if sp and ep:
                    # distance to segment midpoint as proxy
                    mx, my = (sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2
                    d = math.hypot(mx - x, my - y)
                    if d < best_d:
                        best_d = d
                        best_id = e["id"]
            elif e["type"] in ("circle", "arc"):
                cp = point_map.get(e["center"])
                if cp:
                    d = math.hypot(cp[0] - x, cp[1] - y)
                    if d < best_d:
                        best_d = d
                        best_id = e["id"]
            elif e["type"] == "point":
                d = math.hypot(e["x"] - x, e["y"] - y)
                if d < best_d:
                    best_d = d
                    best_id = e["id"]
        return best_id

    for entity in msp.query("DIMENSION"):
        try:
            dimtype = entity.dimtype
            meas = entity.get_measurement()
            if not isinstance(meas, (int, float)):
                continue
            value = float(meas)

            if dimtype in (0, 1):  # linear / aligned
                p1 = entity.dxf.defpoint2
                p2 = entity.dxf.defpoint3
                x1, y1 = float(p1.x), float(p1.y)
                x2, y2 = float(p2.x), float(p2.y)
                # Prefer existing line, else create
                lid = nearest_entity((x1 + x2) / 2, (y1 + y2) / 2, ("line",))
                if not lid:
                    sp = get_or_add_point(x1, y1)
                    ep = get_or_add_point(x2, y2)
                    lid = sketch.add_line(sp, ep)
                dtype = "aligned" if dimtype == 1 else "length"
                sketch.add_dimension(dtype, [lid], value)
            elif dimtype == 4:  # radius
                # center is usually defpoint or defpoint4
                center = getattr(entity.dxf, "defpoint", None) or entity.dxf.defpoint4
                if center:
                    cx, cy = float(center.x), float(center.y)
                    cid = nearest_entity(cx, cy, ("circle", "arc"))
                    if not cid:
                        cpid = get_or_add_point(cx, cy)
                        cid = sketch.add_circle(cpid, max(value, 0.1))
                    sketch.add_radius_dimension(cid, value)
            elif dimtype == 3:  # diameter
                center = getattr(entity.dxf, "defpoint", None) or entity.dxf.defpoint4
                if center:
                    cx, cy = float(center.x), float(center.y)
                    cid = nearest_entity(cx, cy, ("circle", "arc"))
                    if not cid:
                        cpid = get_or_add_point(cx, cy)
                        cid = sketch.add_circle(cpid, max(value / 2, 0.1))
                    sketch.add_diameter_dimension(cid, value)
            elif dimtype == 6:  # ordinate
                # feature location typically defpoint2 or similar
                feat = entity.dxf.defpoint2
                if feat:
                    fx, fy = float(feat.x), float(feat.y)
                    pid = nearest_entity(fx, fy, ("point",))
                    if not pid:
                        pid = get_or_add_point(fx, fy)
                    # axis from dimtype bits or default x
                    axis = "y" if (entity.dxf.get("dimtype", 0) & 64) else "x"
                    sketch.add_ordinate_dimension(pid, value, axis=axis)
            elif dimtype == 2:  # angular (2-line)
                # Typical defpoints for angular_dim_2l:
                # defpoint2/defpoint3 = first line endpoints
                # defpoint4 / another = second line
                # Fall back to creating lines from available points.
                try:
                    pts = []
                    for attr in ("defpoint2", "defpoint3", "defpoint4", "defpoint5", "defpoint"):
                        p = getattr(entity.dxf, attr, None)
                        if p is not None:
                            pts.append((float(p.x), float(p.y)))
                    if len(pts) >= 4:
                        # Pair first two and next two as lines (common pattern)
                        l1_mid = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
                        l2_mid = ((pts[2][0] + pts[3][0]) / 2, (pts[2][1] + pts[3][1]) / 2)
                        lid1 = nearest_entity(l1_mid[0], l1_mid[1], ("line",), tol=1.0)
                        lid2 = nearest_entity(l2_mid[0], l2_mid[1], ("line",), tol=1.0)
                        if not lid1:
                            sp = get_or_add_point(pts[0][0], pts[0][1])
                            ep = get_or_add_point(pts[1][0], pts[1][1])
                            lid1 = sketch.add_line(sp, ep)
                        if not lid2:
                            sp = get_or_add_point(pts[2][0], pts[2][1])
                            ep = get_or_add_point(pts[3][0], pts[3][1])
                            lid2 = sketch.add_line(sp, ep)
                        if lid1 and lid2 and lid1 != lid2:
                            sketch.add_angle_dimension(lid1, lid2, value)
                except Exception:
                    pass
            # future: 3-point angular, etc.
        except Exception:
            continue


def import_dxf_to_sketch(
    path: Union[str, Path],
    *,
    name: str = "Imported Sketch",
    approx_distance: float = 0.1,
    import_dimensions: bool = True,
) -> Sketch:
    """Import LINE, CIRCLE, ARC, LWPOLYLINE, POLYLINE, SPLINE, ELLIPSE, TEXT, and DIMENSION entities from a DXF file into a new Sketch.

    Only modelspace entities of those types are considered. Points are created as needed
    and entities reference them by id. Construction flag is not set. This is a basic
    interchange helper for 2D geometry; full constraint recovery is deferred.

    - LWPOLYLINE / POLYLINE: uses ``virtual_entities()`` so bulge values are converted
      to proper ARC entities (straight segments remain LINE). Closed polylines are handled
      automatically by the virtual entity expansion.
    - SPLINE / ELLIPSE: approximated as connected LINE segments via ``flattening(distance=approx_distance)``.
    - TEXT: creates a point at the insert location; text content is stored in
      ``sketch.metadata["imported_texts"]`` as a list of dicts.
    - DIMENSION (when ``import_dimensions=True``): recovers basic length/aligned, radius,
      diameter, and ordinate dimensions by matching definition points to nearby entities
      (or creating them) and using ``get_measurement()``. Failures are skipped.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"DXF file not found: {path}")

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    sketch = Sketch(name=name)
    # Temporary point cache by rounded coordinate to avoid exact duplicates
    point_cache: dict[tuple[float, float], str] = {}
    imported_texts: list[dict] = []

    def get_or_add_point(x: float, y: float) -> str:
        key = (round(x, 6), round(y, 6))
        if key in point_cache:
            return point_cache[key]
        pid = sketch.add_point(x, y)
        point_cache[key] = pid
        return pid

    def add_from_virtual(entity) -> None:
        """Expand polyline-like entities via virtual LINE/ARC entities."""
        try:
            virtuals = list(entity.virtual_entities())
        except Exception:
            return
        for ve in virtuals:
            vtype = ve.dxftype()
            if vtype == "LINE":
                start = ve.dxf.start
                end = ve.dxf.end
                sp = get_or_add_point(float(start.x), float(start.y))
                ep = get_or_add_point(float(end.x), float(end.y))
                sketch.add_line(sp, ep)
            elif vtype == "ARC":
                center = ve.dxf.center
                cp = get_or_add_point(float(center.x), float(center.y))
                sketch.add_arc(
                    cp,
                    float(ve.dxf.radius),
                    float(ve.dxf.start_angle),
                    float(ve.dxf.end_angle),
                )

    def add_polyline_from_points(points) -> None:
        """Add sequential LINE entities from a list of (x, y) points."""
        if len(points) < 2:
            return
        prev = None
        for pt in points:
            pid = get_or_add_point(float(pt[0]), float(pt[1]))
            if prev is not None:
                sketch.add_line(prev, pid)
            prev = pid

    for entity in msp:
        etype = entity.dxftype()
        if etype == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            sp = get_or_add_point(float(start.x), float(start.y))
            ep = get_or_add_point(float(end.x), float(end.y))
            sketch.add_line(sp, ep)
        elif etype == "CIRCLE":
            center = entity.dxf.center
            cp = get_or_add_point(float(center.x), float(center.y))
            sketch.add_circle(cp, float(entity.dxf.radius))
        elif etype == "ARC":
            center = entity.dxf.center
            cp = get_or_add_point(float(center.x), float(center.y))
            sketch.add_arc(
                cp,
                float(entity.dxf.radius),
                float(entity.dxf.start_angle),
                float(entity.dxf.end_angle),
            )
        elif etype in ("LWPOLYLINE", "POLYLINE"):
            add_from_virtual(entity)
        elif etype == "SPLINE":
            try:
                pts = list(entity.flattening(distance=approx_distance))
                add_polyline_from_points([(p.x, p.y) for p in pts])
            except Exception:
                # Fallback: try path if available
                try:
                    from ezdxf import path
                    pth = path.make_path(entity)
                    pts = list(pth.flattening(distance=approx_distance))
                    add_polyline_from_points([(p.x, p.y) for p in pts])
                except Exception:
                    pass
        elif etype == "ELLIPSE":
            try:
                pts = list(entity.flattening(distance=approx_distance))
                add_polyline_from_points([(p.x, p.y) for p in pts])
            except Exception:
                try:
                    from ezdxf import path
                    pth = path.make_path(entity)
                    pts = list(pth.flattening(distance=approx_distance))
                    add_polyline_from_points([(p.x, p.y) for p in pts])
                except Exception:
                    pass
        elif etype == "TEXT":
            insert = entity.dxf.insert
            pid = get_or_add_point(float(insert.x), float(insert.y))
            imported_texts.append({
                "text": str(entity.dxf.text or ""),
                "x": float(insert.x),
                "y": float(insert.y),
                "height": float(getattr(entity.dxf, "height", 1.0) or 1.0),
                "rotation": float(getattr(entity.dxf, "rotation", 0.0) or 0.0),
                "point_id": pid,
            })

    # DIMENSION import (after geometry so entities exist for matching)
    if import_dimensions:
        _import_dimensions(sketch, msp, get_or_add_point)

    if imported_texts:
        sketch.metadata["imported_texts"] = imported_texts
        sketch.validate()

    return sketch
