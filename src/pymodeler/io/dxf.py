"""DXF export stubs for sketches and 2D profiles using ezdxf.

Provides simple export of Sketch entities and extracted closed profiles
to DXF files suitable for 2D drawings, CNC, or manufacturing workflows.
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
    profile_layer: str = "PROFILES",
    entity_layer: str = "SKETCH",
) -> Path:
    """Export a Sketch to a DXF file.

    - Non-construction entities (lines, circles, arcs) are written to the entity layer.
    - Closed profiles extracted by ``extract_simple_profiles`` are written as
      closed LWPOLYLINEs (polygons) or CIRCLEs on the profile layer.

    Returns the path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc: Drawing = ezdxf.new(dxfversion="R2010")
    msp: Modelspace = doc.modelspace()

    # Layers
    if entity_layer not in doc.layers:
        doc.layers.add(entity_layer, color=7)
    if profile_layer not in doc.layers:
        doc.layers.add(profile_layer, color=1)  # red for profiles

    point_map: dict[str, tuple[float, float]] = {}
    for e in sketch.entities:
        if e["type"] == "point":
            point_map[e["id"]] = (float(e["x"]), float(e["y"]))

    if include_entities:
        _add_entities(msp, sketch, point_map, entity_layer)

    if include_profiles:
        profiles = extract_simple_profiles(sketch)
        _add_profiles(msp, profiles, profile_layer)

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

    doc = ezdxf.new(dxfversion="R2010")
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
) -> Sketch:
    """Import simple LINE, CIRCLE, and ARC entities from a DXF file into a new Sketch.

    Only modelspace entities of those types are considered. Points are created as needed
    and entities reference them by id. Construction flag is not set. This is a basic
    interchange helper for 2D geometry; full constraint/dimension recovery is deferred.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"DXF file not found: {path}")

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    sketch = Sketch(name=name)
    # Temporary point cache by rounded coordinate to avoid exact duplicates
    point_cache: dict[tuple[float, float], str] = {}

    def get_or_add_point(x: float, y: float) -> str:
        key = (round(x, 6), round(y, 6))
        if key in point_cache:
            return point_cache[key]
        pid = sketch.add_point(x, y)
        point_cache[key] = pid
        return pid

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
        # Other entity types (LWPOLYLINE, etc.) deferred for later

    return sketch
