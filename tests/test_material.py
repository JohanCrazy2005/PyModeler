"""Tests for MaterialStore and material schema validation."""

import pytest

from pymodeler.core.material import (
    MaterialStore,
    MaterialValidationError,
    validate_material_data,
    create_default_library,
)


def test_empty_store():
    store = MaterialStore(name="Empty")
    assert store.name == "Empty"
    assert len(store) == 0
    store.validate()


def test_add_and_get():
    store = MaterialStore()
    mat = store.add(
        "Plywood 18mm",
        category="wood",
        type="sheet",
        thickness=18.0,
        grain=True,
        color="#c4a35a",
    )
    assert mat["name"] == "Plywood 18mm"
    assert mat["thickness"] == 18.0
    assert mat["category"] == "wood"
    assert "id" in mat
    assert store.get("Plywood 18mm") is mat
    assert store.get(mat["id"]) is mat
    assert store.names() == ["Plywood 18mm"]


def test_duplicate_name_rejected():
    store = MaterialStore()
    store.add("Oak", category="wood", thickness=20.0)
    with pytest.raises(MaterialValidationError, match="already exists"):
        store.add("Oak", category="wood")


def test_remove():
    store = MaterialStore()
    store.add("Temp", thickness=10.0)
    assert store.remove("Temp") is True
    assert len(store) == 0
    assert store.remove("Temp") is False


def test_update():
    store = MaterialStore()
    store.add("Sheet", thickness=12.0, category="wood")
    updated = store.update("Sheet", thickness=15.0, color="#aabbcc")
    assert updated["thickness"] == 15.0
    assert updated["color"] == "#aabbcc"
    assert store.get("Sheet")["thickness"] == 15.0


def test_update_missing_raises():
    store = MaterialStore()
    with pytest.raises(MaterialValidationError, match="not found"):
        store.update("NoSuch", thickness=1.0)


def test_roundtrip_schema():
    store = MaterialStore(name="Lib")
    store.add(
        "Baltic Birch",
        category="wood",
        type="sheet",
        thickness=18.0,
        width=1220.0,
        length=2440.0,
        density=680.0,
        grain=True,
        unit="mm",
        comment="test stock",
    )
    data = store.to_dict()
    validate_material_data(data)
    restored = MaterialStore.from_dict(data)
    assert restored.name == store.name
    assert len(restored) == 1
    m = restored.get("Baltic Birch")
    assert m is not None
    assert m["thickness"] == 18.0
    assert m["width"] == 1220.0
    assert m["grain"] is True


def test_schema_rejects_bad_category():
    bad = {
        "name": "Bad",
        "materials": [
            {"name": "X", "category": "unobtanium"}
        ],
    }
    with pytest.raises(MaterialValidationError):
        validate_material_data(bad)


def test_schema_rejects_negative_thickness():
    bad = {
        "name": "Bad",
        "materials": [
            {"name": "X", "thickness": -5}
        ],
    }
    with pytest.raises(MaterialValidationError):
        validate_material_data(bad)


def test_default_library():
    lib = create_default_library()
    assert len(lib) >= 3
    birch = lib.get("Baltic Birch 18mm")
    assert birch is not None
    assert birch["thickness"] == 18.0
    assert birch["category"] == "wood"
    lib.validate()


def test_part_can_reference_material_string_or_object():
    """Part.material accepts string or object; ensure material dicts are usable."""
    from pymodeler.core.part import Part

    store = MaterialStore()
    mat = store.add("Test Mat", category="wood", thickness=12.0)

    p1 = Part(name="A", material=mat["name"])
    assert p1.material == "Test Mat"
    p1.validate()

    p2 = Part(name="B", material=mat)
    assert isinstance(p2.material, dict)
    assert p2.material["name"] == "Test Mat"
    p2.validate()

    data = p2.to_dict()
    restored = Part.from_dict(data)
    assert restored.material["name"] == "Test Mat"
