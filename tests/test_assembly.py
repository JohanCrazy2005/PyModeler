"""Tests for the simple Assembly data model."""

import pytest

from pymodeler.core import (
    Assembly,
    Instance,
    Mate,
    Part,
    Transform,
    create_rectangle_sketch,
    ExtrudeFeature,
    FeatureHistory,
)
from pymodeler.core.assembly import AssemblyValidationError, validate_assembly_data


def _make_simple_part(name: str = "Block") -> Part:
    sketch = create_rectangle_sketch(width=10.0, height=10.0, name=f"{name}_sk")
    hist = FeatureHistory(name=f"{name} History")
    hist.add_extrude(ExtrudeFeature(sketch_id=sketch.id, distance=5.0, name="Extrude"))
    return Part(name=name, sketches={sketch.id: sketch}, feature_history=hist)


def test_assembly_create_and_validate():
    part = _make_simple_part("Base")
    asm = Assembly(name="Test Assembly")
    inst = asm.add_instance(part, transform=Transform(location=[10.0, 0.0, 0.0]))
    assert len(asm.instances) == 1
    assert inst.part_id == part.id
    assert inst.transform.location == [10.0, 0.0, 0.0]
    asm.validate()


def test_round_trip_serialization():
    part1 = _make_simple_part("Left")
    part2 = _make_simple_part("Right")
    asm = Assembly(name="Pair")
    asm.add_instance(part1, name="Left Instance", grounded=True)
    asm.add_instance(
        part2,
        transform=Transform(location=[20.0, 0.0, 0.0], rotation=[0.0, 0.0, 1.57]),
        visible=False,
    )

    data = asm.to_dict()
    validate_assembly_data(data)

    parts = {part1.id: part1, part2.id: part2}
    restored = Assembly.from_dict(data, parts=parts)
    assert restored.name == "Pair"
    assert len(restored.instances) == 2
    assert restored.instances[0].grounded is True
    assert restored.instances[1].visible is False
    assert restored.instances[1].transform.location == [20.0, 0.0, 0.0]
    # Runtime part refs restored
    assert restored.instances[0].part is part1
    assert restored.instances[1].part is part2


def test_remove_and_get_instance():
    part = _make_simple_part()
    asm = Assembly()
    inst = asm.add_instance(part)
    assert asm.get_instance(inst.id) is not None
    assert asm.remove_instance(inst.id) is True
    assert len(asm.instances) == 0
    assert asm.remove_instance("missing") is False


def test_invalid_assembly_rejected():
    with pytest.raises(AssemblyValidationError):
        validate_assembly_data({"name": "Bad"})  # missing instances

    with pytest.raises(AssemblyValidationError):
        validate_assembly_data({"instances": [{"foo": "bar"}]})  # missing part_id


def test_instance_defaults():
    part = _make_simple_part()
    asm = Assembly()
    inst = asm.add_instance(part)
    assert inst.transform.location == [0.0, 0.0, 0.0]
    assert inst.transform.rotation == [0.0, 0.0, 0.0]
    assert inst.transform.scale == [1.0, 1.0, 1.0]
    assert inst.grounded is False
    assert inst.visible is True


def test_rigid_mate_schema_and_roundtrip():
    part_a = _make_simple_part("Base")
    part_b = _make_simple_part("Top")
    asm = Assembly(name="Mated")
    ia = asm.add_instance(part_a, name="Base", grounded=True)
    ib = asm.add_instance(part_b, name="Top")
    offset = Transform(location=[0.0, 0.0, 5.0])
    mate = asm.add_mate(ia, ib, type="rigid", offset=offset, name="Stack")
    assert len(asm.mates) == 1
    assert mate.type == "rigid"
    assert mate.instance_a == ia.id
    assert mate.instance_b == ib.id

    data = asm.to_dict()
    validate_assembly_data(data)
    assert "mates" in data
    assert data["mates"][0]["type"] == "rigid"

    parts = {part_a.id: part_a, part_b.id: part_b}
    restored = Assembly.from_dict(data, parts=parts)
    assert len(restored.mates) == 1
    assert restored.mates[0].offset.location == [0.0, 0.0, 5.0]


def test_solve_rigid_mate():
    part_a = _make_simple_part("Anchor")
    part_b = _make_simple_part("Follower")
    asm = Assembly()
    ia = asm.add_instance(part_a, transform=Transform(location=[10.0, 0.0, 0.0]), grounded=True)
    ib = asm.add_instance(part_b, transform=Transform(location=[0.0, 0.0, 0.0]))
    asm.add_mate(ia, ib, type="fastened", offset=Transform(location=[0.0, 20.0, 0.0]))

    # Before solve, B is at origin
    assert ib.transform.location == [0.0, 0.0, 0.0]
    asm.solve_mates()
    # After solve, B should be at A + offset
    assert ib.transform.location == [10.0, 20.0, 0.0]
    # A unchanged
    assert ia.transform.location == [10.0, 0.0, 0.0]


def test_invalid_mate_type():
    with pytest.raises(ValueError):
        Mate(instance_a="a", instance_b="b", type="revolute")
