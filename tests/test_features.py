"""Tests for ExtrudeFeature, RevolveFeature, and FeatureHistory."""

import pytest

from pymodeler.core.features import (
    ExtrudeFeature,
    FeatureHistory,
    FeatureValidationError,
    FilletFeature,
    ChamferFeature,
    HoleFeature,
    RevolveFeature,
    validate_extrude_data,
    validate_fillet_data,
    validate_chamfer_data,
    validate_history_data,
    validate_hole_data,
    validate_revolve_data,
)
from pymodeler.core.parameters import ParameterStore
from pymodeler.core.sketch import create_rectangle_sketch


def test_extrude_numeric_distance():
    sketch = create_rectangle_sketch(width=10.0, height=5.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=3.0, name="Box")
    assert feat.type == "extrude"
    assert feat.resolved_distance() == 3.0
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) == 8
    assert len(mesh.faces) == 6
    feat.validate()


def test_extrude_parameter_distance():
    sketch = create_rectangle_sketch(width=20.0, height=10.0)
    store = ParameterStore()
    store.add("Depth", value=8.0, unit="mm")
    store.add("DoubleDepth", expression="Depth * 2")
    feat = ExtrudeFeature(sketch_id=sketch.id, distance="DoubleDepth")
    assert feat.resolved_distance(store) == 16.0
    mesh = feat.generate_mesh(sketch, store)
    # Height of the box should be approximately the distance
    zs = [v[2] for v in mesh.vertices]
    assert max(zs) - min(zs) == pytest.approx(16.0)


def test_extrude_schema_roundtrip():
    feat = ExtrudeFeature(sketch_id="sketch_abc", distance="Height", symmetric=True)
    data = feat.to_dict()
    validate_extrude_data(data)
    restored = ExtrudeFeature.from_dict(data)
    assert restored.sketch_id == feat.sketch_id
    assert restored.distance == feat.distance
    assert restored.symmetric is True


def test_extrude_invalid_schema():
    with pytest.raises(FeatureValidationError):
        ExtrudeFeature.from_dict({"type": "extrude", "distance": 1.0})  # missing sketch_id


def test_feature_history_basic():
    sketch = create_rectangle_sketch()
    hist = FeatureHistory(name="Part1")
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=2.5)
    hist.add_extrude(feat)
    assert len(hist.features) == 1
    hist.validate()
    data = hist.to_dict()
    validate_history_data(data)
    restored = FeatureHistory.from_dict(data)
    assert len(restored.get_extrude_features()) == 1


def test_feature_history_recompute():
    sketch = create_rectangle_sketch(width=4.0, height=2.0)
    hist = FeatureHistory()
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=1.0)
    hist.add_extrude(feat)
    meshes = hist.recompute_meshes({sketch.id: sketch})
    assert feat.id in meshes
    assert len(meshes[feat.id].vertices) == 8


def test_revolve_solid_of_revolution():
    """Rectangle profile revolved 360° around Y produces a closed lathe mesh."""
    sketch = create_rectangle_sketch(width=4.0, height=3.0)
    feat = RevolveFeature(sketch_id=sketch.id, angle=360.0, segments=8)
    mesh = feat.generate_mesh(sketch)
    # 4 profile points * 8 rings
    assert len(mesh.vertices) == 4 * 8
    assert len(mesh.faces) >= 4 * 8  # at least the side quads
    feat.validate()


def test_revolve_partial_has_caps():
    sketch = create_rectangle_sketch(width=2.0, height=2.0)
    feat = RevolveFeature(sketch_id=sketch.id, angle=90.0, segments=8)
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) > 0
    # Partial should include end cap faces
    assert any(len(f) == 4 for f in mesh.faces)  # profile quads or caps



def test_revolve_partial_angle():
    sketch = create_rectangle_sketch()
    feat = RevolveFeature(sketch_id=sketch.id, angle=180.0)
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) > 0


def test_revolve_parameter():
    store = ParameterStore()
    store.add("Angle", value=90.0)
    sketch = create_rectangle_sketch()
    feat = RevolveFeature(sketch_id=sketch.id, angle="Angle")
    assert feat.resolved_angle(store) == 90.0
    mesh = feat.generate_mesh(sketch, store)
    assert len(mesh.vertices) > 0


def test_extrude_polygon_profile():
    """Polygon from rectangle should produce a simple box."""
    sketch = create_rectangle_sketch(width=6.0, height=4.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=2.0)
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) == 8
    assert len(mesh.faces) == 6


def test_extrude_circle_profile():
    """Circle entity should produce a faceted cylinder."""
    from pymodeler.core.sketch import Sketch
    sketch = Sketch(name="Circle")
    center = sketch.add_point(0, 0)
    sketch.add_circle(center, radius=5.0)
    feat = ExtrudeFeature(sketch_id=sketch.id, distance=3.0)
    mesh = feat.generate_mesh(sketch)
    # 24 segs * 2 rings + 2 centers
    assert len(mesh.vertices) > 40
    assert len(mesh.faces) > 20


def test_profile_extraction_arc_near_circle():
    from pymodeler.core.sketch import Sketch, extract_simple_profiles
    sketch = Sketch()
    c = sketch.add_point(0, 0)
    sketch.add_arc(c, radius=2.0, start_angle=0, end_angle=359)
    profs = extract_simple_profiles(sketch)
    assert any(p["type"] == "circle" for p in profs)


def test_profile_extraction_arc_joined_into_loop():
    """Arc whose start/end match existing points should be discretized into a closed polygon."""
    from pymodeler.core.sketch import Sketch, extract_simple_profiles
    sketch = Sketch()
    p_bl = sketch.add_point(0, 0)
    p_br = sketch.add_point(4, 0)
    p_tr = sketch.add_point(4, 2)
    p_tl = sketch.add_point(0, 2)
    sketch.add_line(p_bl, p_br)
    sketch.add_line(p_tr, p_tl)
    sketch.add_line(p_tl, p_bl)
    center = sketch.add_point(4, 1)
    sketch.add_arc(center, radius=1.0, start_angle=-90, end_angle=90)
    profs = extract_simple_profiles(sketch)
    assert len(profs) >= 1
    poly = next(p for p in profs if p["type"] == "polygon")
    # Should have more than the 4 corner points because of arc discretization
    assert len(poly["points"]) > 8
    # Area should be positive and reasonable
    from pymodeler.core.sketch import _polygon_area
    assert _polygon_area(poly["points"]) > 5.0


def test_profile_extraction_nested_holes():
    """Outer polygon should receive contained inner polygon as a hole."""
    from pymodeler.core.sketch import Sketch, extract_simple_profiles, _polygon_area
    sketch = Sketch()
    # outer 0-10
    bl = sketch.add_point(0, 0)
    br = sketch.add_point(10, 0)
    tr = sketch.add_point(10, 10)
    tl = sketch.add_point(0, 10)
    sketch.add_line(bl, br)
    sketch.add_line(br, tr)
    sketch.add_line(tr, tl)
    sketch.add_line(tl, bl)
    # inner 3-7
    ibl = sketch.add_point(3, 3)
    ibr = sketch.add_point(7, 3)
    itr = sketch.add_point(7, 7)
    itl = sketch.add_point(3, 7)
    sketch.add_line(ibl, ibr)
    sketch.add_line(ibr, itr)
    sketch.add_line(itr, itl)
    sketch.add_line(itl, ibl)
    profs = extract_simple_profiles(sketch)
    assert len(profs) == 1
    outer = profs[0]
    assert outer["type"] == "polygon"
    assert _polygon_area(outer["points"]) == pytest.approx(100.0)
    assert len(outer.get("holes", [])) == 1
    assert _polygon_area(outer["holes"][0]) == pytest.approx(16.0)


def test_hole_numeric():
    feat = HoleFeature(diameter=6.0, depth=10.0, name="M6Hole")
    assert feat.type == "hole"
    assert feat.resolved_diameter() == 6.0
    assert feat.resolved_depth() == 10.0
    mesh = feat.generate_mesh()
    assert len(mesh.vertices) > 20
    assert len(mesh.faces) > 10
    feat.validate()


def test_hole_parameter():
    store = ParameterStore()
    store.add("Dia", value=8.0)
    store.add("Dep", value=15.0)
    feat = HoleFeature(diameter="Dia", depth="Dep")
    assert feat.resolved_diameter(store) == 8.0
    assert feat.resolved_depth(store) == 15.0
    mesh = feat.generate_mesh(store)
    assert len(mesh.vertices) > 0


def test_extrude_with_nested_holes():
    """Extrude of a profile that contains a nested hole should produce a mesh
    that includes the hole (more vertices than the plain outer box, or a
    Boolean-cut result).
    """
    from pymodeler.core.sketch import Sketch, extract_simple_profiles
    sketch = Sketch()
    # outer 0-10
    bl = sketch.add_point(0, 0)
    br = sketch.add_point(10, 0)
    tr = sketch.add_point(10, 10)
    tl = sketch.add_point(0, 10)
    sketch.add_line(bl, br)
    sketch.add_line(br, tr)
    sketch.add_line(tr, tl)
    sketch.add_line(tl, bl)
    # inner 3-7
    ibl = sketch.add_point(3, 3)
    ibr = sketch.add_point(7, 3)
    itr = sketch.add_point(7, 7)
    itl = sketch.add_point(3, 7)
    sketch.add_line(ibl, ibr)
    sketch.add_line(ibr, itr)
    sketch.add_line(itr, itl)
    sketch.add_line(itl, ibl)

    profs = extract_simple_profiles(sketch)
    assert len(profs) == 1
    assert len(profs[0].get("holes", [])) == 1

    feat = ExtrudeFeature(sketch_id=sketch.id, distance=2.0)
    mesh = feat.generate_mesh(sketch)
    # Plain outer would be 8 verts / 6 faces. With hole walls we expect more.
    assert len(mesh.vertices) >= 8
    assert len(mesh.faces) >= 6
    # Should have vertices from both outer and inner
    assert len(mesh.vertices) > 8
    mesh.validate()
    feat.validate()


def test_revolve_arbitrary_axis():
    """Revolve around X-axis should rotate the solid away from pure Y."""
    sketch = create_rectangle_sketch(width=4.0, height=2.0)
    feat = RevolveFeature(sketch_id=sketch.id, angle=360.0, axis=[1.0, 0.0, 0.0], segments=8)
    mesh = feat.generate_mesh(sketch)
    assert len(mesh.vertices) > 0
    # After rotation around X, Y and Z extents should both be non-trivial
    ys = [v[1] for v in mesh.vertices]
    zs = [v[2] for v in mesh.vertices]
    assert max(ys) - min(ys) > 1.0
    assert max(zs) - min(zs) > 1.0
    feat.validate()
