"""Tests for DXF export of sketches and profiles."""

from pathlib import Path

import ezdxf
import pytest

from pymodeler.core.sketch import Sketch, create_rectangle_sketch, extract_simple_profiles
from pymodeler.io.dxf import export_profiles_to_dxf, export_sketch_to_dxf, import_dxf_to_sketch


def test_export_rectangle_sketch(tmp_path: Path):
    sketch = create_rectangle_sketch(width=20.0, height=10.0, name="Rect")
    out = tmp_path / "rect.dxf"
    result = export_sketch_to_dxf(sketch, out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 100

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    lines = list(msp.query("LINE"))
    polylines = list(msp.query("LWPOLYLINE"))
    # Entities produce 4 lines; profiles produce at least one closed polyline
    assert len(lines) >= 4
    assert len(polylines) >= 1
    # Profile layer should exist
    assert "PROFILES" in doc.layers
    assert "SKETCH" in doc.layers


def test_export_circle(tmp_path: Path):
    sketch = Sketch(name="CircleSketch")
    center = sketch.add_point(5.0, 5.0)
    sketch.add_circle(center, radius=3.5)
    out = tmp_path / "circle.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=True, include_entities=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    circles = list(msp.query("CIRCLE"))
    assert len(circles) >= 1
    # Radius should match
    radii = {round(c.dxf.radius, 4) for c in circles}
    assert 3.5 in radii


def test_export_profiles_only(tmp_path: Path):
    sketch = create_rectangle_sketch(8.0, 4.0)
    profiles = extract_simple_profiles(sketch)
    assert any(p["type"] == "polygon" for p in profiles)

    out = tmp_path / "profiles.dxf"
    export_profiles_to_dxf(profiles, out)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    polylines = list(msp.query("LWPOLYLINE"))
    assert len(polylines) >= 1
    # Closed
    for pl in polylines:
        assert pl.closed


def test_export_arc(tmp_path: Path):
    sketch = Sketch(name="ArcSketch")
    center = sketch.add_point(0.0, 0.0)
    sketch.add_arc(center, radius=5.0, start_angle=0.0, end_angle=90.0)
    out = tmp_path / "arc.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False)

    doc = ezdxf.readfile(out)
    arcs = list(doc.modelspace().query("ARC"))
    assert len(arcs) == 1
    assert abs(arcs[0].dxf.radius - 5.0) < 1e-6
    assert abs(arcs[0].dxf.start_angle - 0.0) < 1e-6
    assert abs(arcs[0].dxf.end_angle - 90.0) < 1e-6


def test_no_construction_geometry(tmp_path: Path):
    sketch = Sketch(name="Mixed")
    p1 = sketch.add_point(0, 0)
    p2 = sketch.add_point(10, 0)
    sketch.add_line(p1, p2, construction=True)  # should be skipped
    out = tmp_path / "const.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False)
    doc = ezdxf.readfile(out)
    lines = list(doc.modelspace().query("LINE"))
    assert len(lines) == 0


def test_import_lwpolyline(tmp_path: Path):
    """Import a closed LWPOLYLINE as sequential lines forming a polygon."""
    # Create a simple DXF with a closed LWPOLYLINE rectangle
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    points = [(0, 0), (10, 0), (10, 5), (0, 5)]
    msp.add_lwpolyline(points, close=True)
    dxf_path = tmp_path / "poly.dxf"
    doc.saveas(dxf_path)

    imported = import_dxf_to_sketch(dxf_path, name="PolyImport")
    lines = [e for e in imported.entities if e["type"] == "line"]
    points_ent = [e for e in imported.entities if e["type"] == "point"]
    assert len(points_ent) == 4
    assert len(lines) == 4  # closed rectangle
    # Verify the points roughly match
    coords = sorted([(round(e["x"], 4), round(e["y"], 4)) for e in points_ent])
    assert coords == [(0.0, 0.0), (0.0, 5.0), (10.0, 0.0), (10.0, 5.0)]


def test_import_dxf_roundtrip(tmp_path: Path):
    """Export then import recovers basic line and circle geometry."""
    sketch = Sketch(name="Roundtrip")
    p1 = sketch.add_point(0.0, 0.0)
    p2 = sketch.add_point(10.0, 0.0)
    sketch.add_line(p1, p2)
    c = sketch.add_point(5.0, 5.0)
    sketch.add_circle(c, 2.0)

    out = tmp_path / "rt.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False)

    imported = import_dxf_to_sketch(out, name="Imported")
    assert imported.name == "Imported"
    # Should have points and the line + circle
    lines = [e for e in imported.entities if e["type"] == "line"]
    circles = [e for e in imported.entities if e["type"] == "circle"]
    assert len(lines) == 1
    assert len(circles) == 1
    assert abs(circles[0]["radius"] - 2.0) < 1e-6
    # Endpoints of the line should match approximately
    pts = {e["id"]: (e["x"], e["y"]) for e in imported.entities if e["type"] == "point"}
    line = lines[0]
    start = pts[line["start_point"]]
    end = pts[line["end_point"]]
    assert abs(start[0] - 0.0) < 1e-4 or abs(start[0] - 10.0) < 1e-4
    assert abs(end[0] - 0.0) < 1e-4 or abs(end[0] - 10.0) < 1e-4
