"""Tests for basic BOM generation."""

import pytest

from pymodeler.core import (
    Assembly,
    ExtrudeFeature,
    FeatureHistory,
    MaterialStore,
    Part,
    create_default_library,
    create_rectangle_sketch,
)
from pymodeler.core.bom import (
    BOM,
    BOMValidationError,
    bom_to_csv,
    bom_to_text,
    generate_bom,
    validate_bom_data,
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


def test_generate_bom_from_parts():
    part = _make_plate("Shelf", 600.0, 400.0, 18.0, material="Baltic Birch 18mm")
    bom = generate_bom(parts=part)
    validate_bom_data(bom)
    assert bom["source"] == "parts"
    assert len(bom["items"]) == 1
    item = bom["items"][0]
    assert item["name"] == "Shelf"
    assert item["quantity"] == 1
    assert item["has_geometry"] is True
    assert item["size"]["width"] == pytest.approx(600.0)
    assert item["size"]["depth"] == pytest.approx(400.0)
    assert item["size"]["height"] == pytest.approx(18.0)
    assert item["material_name"] == "Baltic Birch 18mm"


def test_bom_quantities_and_material_store():
    store = create_default_library()
    p1 = _make_plate("Side", 700.0, 400.0, 19.0, material="MDF 19mm")
    p2 = _make_plate("Back", 700.0, 300.0, 6.0, material="Acrylic 6mm")
    qtys = {p1.id: 2, p2.id: 1}
    bom = generate_bom([p1, p2], material_store=store, quantities=qtys, name="Cabinet BOM")
    assert len(bom["items"]) == 2
    by_name = {it["name"]: it for it in bom["items"]}
    assert by_name["Side"]["quantity"] == 2
    assert by_name["Back"]["quantity"] == 1
    assert by_name["Side"]["material_name"] == "MDF 19mm"
    assert by_name["Side"]["material_id"] is not None


def test_bom_from_assembly():
    side = _make_plate("Side", 500.0, 300.0, 18.0, material="Plywood 18mm")
    shelf = _make_plate("Shelf", 400.0, 200.0, 18.0, material="Plywood 18mm")
    asm = Assembly(name="Cabinet")
    asm.add_instance(side, name="Left")
    asm.add_instance(side, name="Right")  # second instance of same part
    asm.add_instance(shelf, name="Top")
    parts_map = {side.id: side, shelf.id: shelf}
    bom = generate_bom(assembly=asm, parts_map=parts_map, name="Assembly BOM")
    validate_bom_data(bom)
    assert bom["source"] == "assembly"
    by_name = {it["name"]: it for it in bom["items"]}
    assert by_name["Side"]["quantity"] == 2
    assert by_name["Shelf"]["quantity"] == 1
    assert by_name["Side"]["has_geometry"] is True


def test_bom_class_and_exports():
    part = _make_plate("Block", 10.0, 10.0, 10.0)
    bom_obj = BOM.from_parts(part, name="Test BOM")
    text = bom_obj.to_text()
    assert "Test BOM" in text
    assert "Block" in text
    assert "Total unique parts: 1" in text
    csv = bom_obj.to_csv()
    assert "quantity,name,material_name" in csv
    assert "Block" in csv
    data = bom_obj.to_dict()
    validate_bom_data(data)


def test_empty_and_unresolved():
    empty = Part(name="Empty", material={"name": "Custom"})
    bom = generate_bom(parts=empty)
    item = bom["items"][0]
    assert item["has_geometry"] is False
    assert "size" not in item
    assert item["material_name"] == "Custom"

    # Assembly with unknown part_id
    asm = Assembly()
    # Manually inject an instance without a Part object
    from pymodeler.core.assembly import Instance
    asm.instances.append(Instance(part_id="unknown_part", name="Mystery"))
    asm.validate()
    bom2 = generate_bom(assembly=asm)
    assert len(bom2["items"]) == 1
    assert bom2["items"][0]["part_id"] == "unknown_part"
    assert bom2["items"][0]["has_geometry"] is False


def test_invalid_bom_rejected():
    with pytest.raises(BOMValidationError):
        validate_bom_data({"name": "Bad"})  # missing items
