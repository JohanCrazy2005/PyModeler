"""Tests for Material / stock store."""

import pytest

from pymodeler.core import MaterialStore, MaterialValidationError


def test_material_store_creation_and_add():
    store = MaterialStore(name="Shop Stock")
    assert store.name == "Shop Stock"
    assert len(store.materials) == 0

    mat = store.add(
        "18mm Plywood",
        thickness=18.0,
        type="plywood",
        unit="mm",
        cost=45.0,
        comment="Standard cabinet carcass",
    )
    assert mat["name"] == "18mm Plywood"
    assert mat["thickness"] == 18.0
    assert len(store.materials) == 1

    got = store.get("18mm Plywood")
    assert got is not None
    assert got["type"] == "plywood"

    names = store.names()
    assert "18mm Plywood" in names


def test_material_store_roundtrip():
    store = MaterialStore()
    store.add("MDF 12mm", thickness=12.0, type="mdf")
    store.add("Aluminum Sheet", thickness=2.0, type="aluminum", density=2700.0)

    data = store.to_dict()
    restored = MaterialStore.from_dict(data)

    assert restored.name == store.name
    assert len(restored.materials) == 2
    assert restored.get("MDF 12mm")["thickness"] == 12.0
    assert restored.get("Aluminum Sheet")["density"] == 2700.0


def test_material_store_validation():
    # Empty name should fail
    with pytest.raises(MaterialValidationError):
        store = MaterialStore()
        store.add("", thickness=10.0)

    # Negative thickness should fail schema
    with pytest.raises(MaterialValidationError):
        store = MaterialStore()
        store.materials.append({"name": "Bad", "thickness": -1.0})
        store.validate()


def test_material_replace_by_name():
    store = MaterialStore()
    store.add("Oak", thickness=19.0, type="solid_wood")
    store.add("Oak", thickness=25.0, type="solid_wood", comment="thicker stock")
    assert len(store.materials) == 1
    assert store.get("Oak")["thickness"] == 25.0
    assert store.get("Oak")["comment"] == "thicker stock"
