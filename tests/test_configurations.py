"""Tests for ConfigurationSet (independent inputs)."""

import pytest

from pymodeler.core import (
    Part,
    ParameterStore,
    Sketch,
    ExtrudeFeature,
    ConfigurationSet,
    ConfigurationValidationError,
)
from pymodeler.core.sketch import create_rectangle_sketch


def test_configuration_schema_and_roundtrip():
    cfg = ConfigurationSet(name="Size Variants")
    cfg.add_list_input(
        "Size",
        options=[
            {"name": "Small", "parameter_overrides": {"length": 10.0}},
            {"name": "Large", "parameter_overrides": {"length": 50.0}},
        ],
    )
    cfg.add_numeric_input("CustomLength", "length", min_val=5.0, max_val=100.0, default=20.0)
    cfg.add_boolean_input("WithHole", target_feature="hole_feat")

    data = cfg.to_dict()
    restored = ConfigurationSet.from_dict(data)
    assert restored.name == "Size Variants"
    assert len(restored.inputs) == 3
    assert restored.get_input("Size")["type"] == "list"


def test_apply_list_and_numeric_to_part():
    part = Part(name="Box")
    sk = create_rectangle_sketch(width=10, height=10)
    part.add_sketch(sk)
    part.parameters.add("length", value=10.0)
    extrude = ExtrudeFeature(sketch_id=sk.id, distance="length", name="Base")
    part.feature_history.add_extrude(extrude)

    cfg = ConfigurationSet()
    cfg.add_list_input(
        "Size",
        options=[
            {"name": "Small", "parameter_overrides": {"length": 5.0}},
            {"name": "Large", "parameter_overrides": {"length": 30.0}},
        ],
    )
    cfg.add_numeric_input("Custom", "length", min_val=1.0, max_val=100.0)

    part.configurations = cfg

    # Apply list
    cfg.apply(part, {"Size": "Large"})
    assert part.parameters.evaluate("length") == 30.0

    # Apply numeric
    cfg.apply(part, {"Custom": 42.0})
    assert part.parameters.evaluate("length") == 42.0

    # Bounds
    with pytest.raises(ConfigurationValidationError):
        cfg.apply(part, {"Custom": 200.0})


def test_boolean_suppresses_feature():
    part = Part(name="WithOptional")
    sk = create_rectangle_sketch(width=10, height=10)
    part.add_sketch(sk)
    base = ExtrudeFeature(sketch_id=sk.id, distance=5.0, name="Base")
    hole = ExtrudeFeature(sketch_id=sk.id, distance=10.0, name="Hole")
    part.feature_history.add_extrude(base)
    part.feature_history.add_extrude(hole)
    hole_id = hole.id

    cfg = ConfigurationSet()
    cfg.add_boolean_input("IncludeHole", target_feature=hole_id, suppress_when_false=True)

    # Suppress
    cfg.apply(part, {"IncludeHole": False})
    meshes = part.feature_history.recompute_meshes(part.sketches, part.parameters)
    assert hole_id not in meshes
    assert any(f.get("id") == base.id for f in part.feature_history.features)

    # Unsuppress
    cfg.apply(part, {"IncludeHole": True})
    meshes = part.feature_history.recompute_meshes(part.sketches, part.parameters)
    assert hole_id in meshes


def test_part_roundtrip_with_configurations():
    part = Part(name="Configured")
    cfg = ConfigurationSet(name="Family")
    cfg.add_list_input(
        "Variant",
        options=[{"name": "A", "parameter_overrides": {"w": 1.0}}],
    )
    part.configurations = cfg
    data = part.to_dict()
    restored = Part.from_dict(data)
    assert restored.configurations is not None
    assert restored.configurations.name == "Family"
    assert len(restored.configurations.inputs) == 1
