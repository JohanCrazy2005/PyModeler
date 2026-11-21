"""Tests for Mesh.bevel_edges and Fillet/Chamfer apply_to_mesh integration."""

import pytest

from pymodeler.core.mesh import Mesh, create_cube
from pymodeler.core.features_more import FilletFeature, ChamferFeature
from pymodeler.core.parameters import ParameterStore
from pymodeler.core.part import Part
from pymodeler.core.features_more import FeatureHistory
from pymodeler.core.sketch import create_rectangle_sketch
from pymodeler.core.features import ExtrudeFeature


def test_get_unique_edges_cube():
    mesh = create_cube(size=2.0)
    edges = mesh.get_unique_edges()
    assert len(edges) == 12
    for a, b in edges:
        assert a < b


def test_edge_face_map_cube():
    mesh = create_cube(size=2.0)
    ef = mesh.edge_face_map()
    assert len(ef) == 12
    for faces in ef.values():
        assert len(faces) == 2


def test_bevel_edges_all_on_cube():
    mesh = create_cube(size=2.0)
    beveled = mesh.bevel_edges(amount=0.15, segments=1)
    beveled.validate()
    assert len(mesh.vertices) == 8
    assert len(mesh.faces) == 6
    assert len(beveled.vertices) > 8
    assert len(beveled.faces) > 6


def test_bevel_edges_selected():
    mesh = create_cube(size=2.0)
    edges = mesh.get_unique_edges()
    beveled = mesh.bevel_edges(edges=edges[:2], amount=0.1)
    beveled.validate()
    assert len(beveled.vertices) > 8


def test_bevel_edges_by_index():
    mesh = create_cube(size=2.0)
    beveled = mesh.bevel_edges(edges=[0, 1, 2], amount=0.1)
    beveled.validate()
    assert len(beveled.faces) > 6


def test_bevel_corner_fans_and_cleanup():
    """Improved bevel produces corner fans and survives cleanup on a cube."""
    mesh = create_cube(size=2.0)
    beveled = mesh.bevel_edges(amount=0.12, segments=1, cleanup=True)
    beveled.validate()
    # Corner fans + chamfer faces should increase face count substantially
    assert len(beveled.faces) > 12
    # Cleanup should not leave the mesh empty
    assert len(beveled.vertices) > 8
    # Calling without cleanup still validates
    raw = mesh.bevel_edges(amount=0.12, cleanup=False)
    raw.validate()
    assert len(raw.vertices) >= len(beveled.vertices)

    mesh = create_cube(size=2.0)
    with pytest.raises(ValueError):
        mesh.bevel_edges(amount=0.0)


def test_bevel_fillet_segments():
    mesh = create_cube(size=2.0)
    beveled = mesh.bevel_edges(amount=0.2, segments=4)
    beveled.validate()
    assert len(beveled.vertices) > len(mesh.bevel_edges(amount=0.2, segments=1).vertices)


def test_chamfer_feature_constructs():
    feat = ChamferFeature(distance=0.25, name="ChamferTop")
    assert feat.type == "chamfer"
    assert feat.operation == "modify"
    assert feat.resolved_distance() == 0.25
    feat.validate()
    data = feat.to_dict()
    assert data["operation"] == "modify"
    roundtrip = ChamferFeature.from_dict(data)
    assert roundtrip.resolved_distance() == 0.25


def test_fillet_feature_constructs():
    feat = FilletFeature(radius=0.3, name="FilletEdges")
    assert feat.type == "fillet"
    assert feat.operation == "modify"
    assert feat.resolved_radius() == 0.3
    feat.validate()


def test_chamfer_apply_to_mesh():
    mesh = create_cube(size=2.0)
    feat = ChamferFeature(distance=0.15)
    result = feat.apply_to_mesh(mesh)
    result.validate()
    assert len(result.vertices) > 8
    assert len(result.faces) > 6


def test_fillet_apply_to_mesh():
    mesh = create_cube(size=2.0)
    feat = FilletFeature(radius=0.12)
    result = feat.apply_to_mesh(mesh)
    result.validate()
    assert len(result.vertices) > 8


def test_chamfer_parameter_distance():
    store = ParameterStore()
    store.add("ChamferDist", value=0.2)
    feat = ChamferFeature(distance="ChamferDist")
    assert feat.resolved_distance(store) == 0.2
    mesh = create_cube()
    result = feat.apply_to_mesh(mesh, store)
    result.validate()


def test_part_recompute_with_chamfer():
    # Minimal integration: extrude then chamfer on part
    sketch = create_rectangle_sketch(width=4.0, height=3.0)
    extrude = ExtrudeFeature(sketch_id=sketch.id, distance=2.0)
    chamfer = ChamferFeature(distance=0.2, name="EdgeBreak")
    history = FeatureHistory()
    history.add_extrude(extrude)
    history.add_chamfer(chamfer)
    part = Part(name="ChamferedBox")
    part.add_sketch(sketch)
    part.feature_history = history
    part.recompute()
    body = part.get_body()
    assert body is not None
    assert len(body.vertices) > 8


def test_part_recompute_with_fillet():
    sketch = create_rectangle_sketch(width=5.0, height=5.0)
    extrude = ExtrudeFeature(sketch_id=sketch.id, distance=2.0)
    fillet = FilletFeature(radius=0.15)
    history = FeatureHistory()
    history.add_extrude(extrude)
    history.add_fillet(fillet)
    part = Part(name="FilletedBox")
    part.add_sketch(sketch)
    part.feature_history = history
    part.recompute()
    body = part.get_body()
    assert body is not None
    assert len(body.vertices) > 8


def test_chamfer_generate_mesh_placeholder():
    feat = ChamferFeature(distance=1.0)
    mesh = feat.generate_mesh()
    mesh.validate()
    assert len(mesh.vertices) > 0


def test_chamfer_two_distance_mode():
    feat = ChamferFeature(distance=0.2, mode="two_distance", distance2=0.4, name="TwoDist")
    assert feat.mode == "two_distance"
    assert feat.resolved_distance2() == 0.4
    feat.validate()
    data = feat.to_dict()
    assert data["mode"] == "two_distance"
    assert data["distance2"] == 0.4
    roundtrip = ChamferFeature.from_dict(data)
    assert roundtrip.resolved_distance2() == 0.4

    mesh = create_cube(size=2.0)
    result = feat.apply_to_mesh(mesh)
    result.validate()
    assert len(result.vertices) > 8


def test_chamfer_distance_angle_mode():
    feat = ChamferFeature(distance=0.3, mode="distance_angle", angle=45.0)
    assert feat.resolved_angle() == 45.0
    feat.validate()
    mesh = create_cube()
    result = feat.apply_to_mesh(mesh)
    result.validate()
    assert len(result.faces) > 6
