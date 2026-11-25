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
    """Add basic DIMENSION entities for sketch dimensions.

    Supports:
    - length / distance on a line (linear dimension, offset slightly above)
    - radius on circle or arc
    - diameter on circle or arc
    - angle between two lines (2-line angular)
    """
    entity_by_id = {e["id"]: e for e in sketch.entities}

    for dim in sketch.dimensions:
        dtype = dim.get("type")
        ents = dim.get("entities", [])
        if not ents:
            continue
        try:
            if dtype in ("length", "distance") and len(ents) >= 1:
                # Prefer first entity if it is a line
                eid = ents[0]
                ent = entity_by_id.get(eid)
                if ent and ent["type"] == "line":
                    start = point_map.get(ent["start_point"])
                    end = point_map.get(ent["end_point"])
                    if start and end:
                        # Offset the dimension line a bit perpendicular
                        dx = end[0] - start[0]
                        dy = end[1] - start[1]
                        length = math.hypot(dx, dy) or 1.0
                        # Perp unit vector
                        px, py = -dy / length, dx / length
                        offset = 5.0  # fixed offset for stub
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
                        # Place radius dim at 45 degrees
                        dim_ent = msp.add_radius_dim(
                            center=center,
                            radius=radius,
                            angle=45.0,
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
                        # Place diameter dim at 45 degrees
                        dim_ent = msp.add_diameter_dim(
                            center=center,
                            radius=radius,
                            angle=45.0,
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
                        # Simple base near the midpoints, offset a bit
                        mid1 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                        mid2 = ((p3[0] + p4[0]) / 2, (p3[1] + p4[1]) / 2)
                        base = (
                            (mid1[0] + mid2[0]) / 2 + 5.0,
                            (mid1[1] + mid2[1]) / 2 + 5.0,
                        )
                        dim_ent = msp.add_angular_dim_2l(
                            base=base,
                            line1=(p1, p2),
                            line2=(p3, p4),
                            dimstyle="EZ_CURVED",
                            dxfattribs={"layer": layer},
                        )
                        dim_ent.render()
            # future: better placement, angular by 3 points, etc.
        except Exception:
            # Skip dimensions that fail to render (stub robustness)
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


def import_dxf_to_sketch(
    path: Union[str, Path],
    *,
    name: str = "Imported Sketch",
    approx_distance: float = 0.1,
) -> Sketch:
    """Import LINE, CIRCLE, ARC, LWPOLYLINE, POLYLINE, SPLINE, ELLIPSE, and TEXT entities from a DXF file into a new Sketch.

    Only modelspace entities of those types are considered. Points are created as needed
    and entities reference them by id. Construction flag is not set. This is a basic
    interchange helper for 2D geometry; full constraint/dimension recovery is deferred.

    - LWPOLYLINE / POLYLINE: uses ``virtual_entities()`` so bulge values are converted
      to proper ARC entities (straight segments remain LINE). Closed polylines are handled
      automatically by the virtual entity expansion.
    - SPLINE / ELLIPSE: approximated as connected LINE segments via ``flattening(distance=approx_distance)``.
    - TEXT: creates a point at the insert location; text content is stored in
      ``sketch.metadata["imported_texts"]`` as a list of dicts.
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

    if imported_texts:
        sketch.metadata["imported_texts"] = imported_texts
        sketch.validate()

    return sketch
