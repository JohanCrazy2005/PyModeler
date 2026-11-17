"""Tests for cut-list generation."""

import pytest

from pymodeler.core import (
    ExtrudeFeature,
    FeatureHistory,
    MaterialStore,
    Part,
    create_default_library,
    create_rectangle_sketch,
)
from pymodeler.core.cutlist import (
    CutList,
    CutListValidationError,
    cut_list_to_text,
    generate_cut_list,
    validate_cutlist_data,
)


def _make_plate(name: str, width: float, height: float, thickness: float, material=None) -> Part:
    sketch = create_rectangle_sketch(width=width, height=height, name=f"{name}_sk")
    hist = FeatureHistory(name=f"{name} History")
    hist.add_extrude(ExtrudeFeature(sketch_id=sketch.id, distance=thickness, name="Extrude"))
    return Part(
        name=name,
        sketches={sketch.id: sketch},
        feature_history=hist,
        material=material,
    )


def test_generate_cut_list_basic():
    part = _make_plate("Shelf", 600.0, 400.0, 18.0, material="Baltic Birch 18mm")
    cl = generate_cut_list(part)
    validate_cutlist_data(cl)
    assert len(cl["items"]) == 1
    item = cl["items"][0]
    assert item["name"] == "Shelf"
    assert item["quantity"] == 1
    assert item["has_geometry"] is True
    # Extrude along Z of a rectangle in XY → size approx 600 x 400 x 18
    assert item["size"]["width"] == pytest.approx(600.0)
    assert item["size"]["depth"] == pytest.approx(400.0)
    assert item["size"]["height"] == pytest.approx(18.0)
    assert item["material_name"] == "Baltic Birch 18mm"  # unresolved string


def test_material_store_resolution():
    store = create_default_library()
    part = _make_plate("Panel", 100.0, 50.0, 18.0, material="Baltic Birch 18mm")
    cl = generate_cut_list([part], material_store=store)
    item = cl["items"][0]
    assert item["material_name"] == "Baltic Birch 18mm"
    assert item["material_id"] is not None
    assert item["size"]["height"] == pytest.approx(18.0)


def test_multiple_parts_and_quantities():
    p1 = _make_plate("Side", 700.0, 400.0, 19.0, material="MDF 19mm")
    p2 = _make_plate("Back", 700.0, 300.0, 6.0, material="Acrylic 6mm")
    store = create_default_library()
    qtys = {p1.id: 2, p2.id: 1}
    cl = generate_cut_list([p1, p2], material_store=store, quantities=qtys, name="Cabinet Parts")
    assert len(cl["items"]) == 2
    assert cl["items"][0]["quantity"] == 2
    assert cl["items"][1]["quantity"] == 1
    assert cl["items"][0]["material_name"] == "MDF 19mm"
    assert cl["items"][1]["material_name"] == "Acrylic 6mm"


def test_empty_part_and_object_material():
    empty = Part(name="Empty", material={"name": "Custom Steel", "thickness": 3.0})
    cl = generate_cut_list(empty)
    item = cl["items"][0]
    assert item["has_geometry"] is False
    assert "size" not in item or item.get("size") is None
    assert item["material_name"] == "Custom Steel"


def test_cutlist_class_and_text():
    part = _make_plate("Block", 10.0, 10.0, 10.0)
    cl_obj = CutList.from_parts(part, name="Test List")
    text = cl_obj.to_text()
    assert "Test List" in text
    assert "Block" in text
    assert "10.0" in text
    assert "Total unique parts: 1" in text
    data = cl_obj.to_dict()
    validate_cutlist_data(data)


def test_invalid_cutlist_rejected():
    with pytest.raises(CutListValidationError):
        validate_cutlist_data({"name": "Bad"})  # missing items
