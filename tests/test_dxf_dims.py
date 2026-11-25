"""Tests for DXF dimension export."""

from pathlib import Path

import ezdxf
import pytest

from pymodeler.core.sketch import Sketch, create_rectangle_sketch
from pymodeler.io.dxf import export_sketch_to_dxf


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
    sketch = Sketch(name="DiamDim")
    center = sketch.add_point(0.0, 0.0)
    circ = sketch.add_circle(center, radius=4.0)
    sketch.add_diameter_dimension(circ, 8.0)
    out = tmp_path / "diam_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 1
    assert any(d.dimtype == 3 for d in dims)  # 3 = diameter


def test_export_with_angle_dimension(tmp_path: Path):
    sketch = Sketch(name="AngleDim")
    # Two lines forming an angle
    p0 = sketch.add_point(0.0, 0.0)
    p1 = sketch.add_point(5.0, 0.0)
    p2 = sketch.add_point(0.0, 5.0)
    ln1 = sketch.add_line(p0, p1)
    ln2 = sketch.add_line(p0, p2)
    sketch.add_angle_dimension(ln1, ln2, 90.0)
    out = tmp_path / "angle_dim.dxf"
    export_sketch_to_dxf(sketch, out, include_profiles=False, include_dimensions=True)

    doc = ezdxf.readfile(out)
    msp = doc.modelspace()
    dims = list(msp.query("DIMENSION"))
    assert len(dims) >= 1
    assert any(d.dimtype == 2 for d in dims)  # 2 = angular 2-line
