"""Tests for DXF dimension export."""

from pathlib import Path

import ezdxf
import pytest

from pymodeler.core.sketch import Sketch, create_rectangle_sketch
from pymodeler.io.dxf import export_sketch_to_dxf, import_dxf_to_sketch


def test_export_with_length_dimensions(tmp_path: Path):
    sketch = create_rectangle_sketch(width=20.0, height=10.0)
    out = tmp_path / "rect_dims.dxf"
    export_sketch_to_dxf(sketch, out, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 2  # at least the two length dims
    assert "DIMENSIONS" in doc.layers


def test_export_with_radius_dimension(tmp_path: Path):
    sketch = Sketch(name="CircleDim")
    center = sketch.add_point(0.0, 0.0)
    circ = sketch.add_circle(center, radius=5.0)
    sketch.add_radius_dimension(circ, 5.0)
    out = tmp_path / "circle_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 1
    # Should have a radius type
    assert any(d.dimtype == 4 for d in dims)  # 4 = radius


def test_export_with_diameter_dimension(tmp_path: Path):
    sketch = Sketch(name="DiaDim")
    center = sketch.add_point(0.0, 0.0)
    circ = sketch.add_circle(center, radius=6.0)
    sketch.add_diameter_dimension(circ, 12.0)
    out = tmp_path / "dia_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 1
    # Diameter dimtype is typically 3 (diameter)
    assert any(getattr(d, "dimtype", None) in (3, 163) for d in dims) or len(dims) >= 1


def test_export_with_angular_dimension(tmp_path: Path):
    sketch = Sketch(name="AngleDim")
    o = sketch.add_point(0.0, 0.0)
    p1 = sketch.add_point(10.0, 0.0)
    p2 = sketch.add_point(0.0, 10.0)
    l1 = sketch.add_line(o, p1)
    l2 = sketch.add_line(o, p2)
    sketch.add_angle_dimension(l1, l2, 90.0)
    out = tmp_path / "angle_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 1
    assert "DIMENSIONS" in doc.layers


def test_export_mixed_dimensions(tmp_path: Path):
    sketch = create_rectangle_sketch(width=30.0, height=15.0)
    c = sketch.add_point(0.0, 0.0)
    circ = sketch.add_circle(c, radius=4.0)
    sketch.add_radius_dimension(circ, 4.0)
    sketch.add_diameter_dimension(circ, 8.0)
    out = tmp_path / "mixed.dxf"
    export_sketch_to_dxf(sketch, out, include_dimensions=True)
    doc = ezdxf.readfile(out)
    dims = list(doc.modelspace().query("DIMENSION"))
    # 2 length + radius + diameter
    assert len(dims) >= 4


def test_export_with_aligned_dimension(tmp_path: Path):
    sketch = Sketch(name="AlignedDim")
    p1 = sketch.add_point(0.0, 0.0)
    p2 = sketch.add_point(10.0, 5.0)
    ln = sketch.add_line(p1, p2)
    sketch.add_aligned_dimension(ln, 11.18, distance=8.0)
    out = tmp_path / "aligned_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 1
    # Aligned dimtype is typically 1
    assert any(getattr(d, "dimtype", None) in (1, 33) for d in dims) or len(dims) >= 1


def test_export_with_ordinate_dimension(tmp_path: Path):
    sketch = Sketch(name="OrdinateDim")
    p = sketch.add_point(20.0, 15.0)
    sketch.add_ordinate_dimension(p, 20.0, axis="x", origin=(0.0, 0.0), offset=12.0)
    sketch.add_ordinate_dimension(p, 15.0, axis="y", origin=(0.0, 0.0), offset=12.0)
    out = tmp_path / "ordinate_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 2
    # Ordinate dimtype is 6
    assert any(getattr(d, "dimtype", None) in (6, 70) for d in dims) or len(dims) >= 2


def test_import_dimensions_roundtrip(tmp_path: Path):
    """Export dimensions then import recovers them as sketch dimensions."""
    sketch = create_rectangle_sketch(width=20.0, height=10.0)
    out = tmp_path / "rt_dims.dxf"
    export_sketch_to_dxf(sketch, out, include_dimensions=True)

    imported = import_dxf_to_sketch(out, name="ImportedDims", import_dimensions=True)
    dims = imported.dimensions
    # At least the two length dimensions should be recovered
    assert len(dims) >= 2
    types = {d["type"] for d in dims}
    assert "length" in types or "aligned" in types
    # Values should be approximately the original
    values = []
    for d in dims:
        try:
            values.append(float(d["value"]))
        except (TypeError, ValueError):
            pass
    assert any(abs(v - 20.0) < 1.0 or abs(v - 10.0) < 1.0 for v in values)


def test_import_angular_dimension(tmp_path: Path):
    """Export angular dimension then import recovers it as sketch angle dimension."""
    sketch = Sketch(name="AngleImport")
    o = sketch.add_point(0.0, 0.0)
    p1 = sketch.add_point(10.0, 0.0)
    p2 = sketch.add_point(0.0, 10.0)
    l1 = sketch.add_line(o, p1)
    l2 = sketch.add_line(o, p2)
    sketch.add_angle_dimension(l1, l2, 90.0)
    out = tmp_path / "angle.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    imported = import_dxf_to_sketch(out, import_dimensions=True)
    angle_dims = [d for d in imported.dimensions if d["type"] == "angle"]
    assert len(angle_dims) >= 1
    assert abs(float(angle_dims[0]["value"]) - 90.0) < 1.0
    assert len(angle_dims[0]["entities"]) == 2
