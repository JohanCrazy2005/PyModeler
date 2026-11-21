"""Tests for SheetMetalRuleStore, bend allowance, and schema validation."""

import math

import pytest

from pymodeler.core.sheet_metal import (
    SheetMetalRuleStore,
    SheetMetalRuleValidationError,
    validate_sheet_metal_rule_data,
    bend_allowance,
    create_default_sheet_metal_rules,
)


def test_empty_store():
    store = SheetMetalRuleStore(name="Empty")
    assert store.name == "Empty"
    assert len(store) == 0
    store.validate()


def test_add_and_get():
    store = SheetMetalRuleStore()
    rule = store.add(
        "Test 1.2mm",
        thickness=1.2,
        bend_radius=1.0,
        k_factor=0.40,
        relief_type="rectangular",
    )
    assert rule["name"] == "Test 1.2mm"
    assert rule["thickness"] == 1.2
    assert rule["k_factor"] == 0.40
    assert "id" in rule
    assert store.get("Test 1.2mm") is rule
    assert store.get(rule["id"]) is rule
    assert store.names() == ["Test 1.2mm"]


def test_duplicate_name_rejected():
    store = SheetMetalRuleStore()
    store.add("Steel", thickness=1.0, bend_radius=1.0, k_factor=0.4)
    with pytest.raises(SheetMetalRuleValidationError, match="already exists"):
        store.add("Steel", thickness=2.0, bend_radius=2.0, k_factor=0.4)


def test_remove():
    store = SheetMetalRuleStore()
    store.add("Temp", thickness=1.0, bend_radius=1.0, k_factor=0.4)
    assert store.remove("Temp") is True
    assert len(store) == 0
    assert store.remove("Temp") is False


def test_roundtrip_schema():
    store = SheetMetalRuleStore(name="Lib")
    store.add(
        "Alu 1.5",
        thickness=1.5,
        bend_radius=1.5,
        k_factor=0.38,
        unit="mm",
        comment="test",
    )
    data = store.to_dict()
    validate_sheet_metal_rule_data(data)
    restored = SheetMetalRuleStore.from_dict(data)
    assert restored.name == store.name
    assert len(restored) == 1
    r = restored.get("Alu 1.5")
    assert r is not None
    assert r["thickness"] == 1.5
    assert r["k_factor"] == 0.38


def test_schema_rejects_bad_k_factor():
    bad = {
        "name": "Bad",
        "rules": [
            {
                "name": "X",
                "thickness": 1.0,
                "bend_radius": 1.0,
                "k_factor": 0.8,  # > 0.5
            }
        ],
    }
    with pytest.raises(SheetMetalRuleValidationError):
        validate_sheet_metal_rule_data(bad)


def test_schema_rejects_non_positive_thickness():
    bad = {
        "name": "Bad",
        "rules": [
            {
                "name": "X",
                "thickness": 0,
                "bend_radius": 1.0,
                "k_factor": 0.4,
            }
        ],
    }
    with pytest.raises(SheetMetalRuleValidationError):
        validate_sheet_metal_rule_data(bad)


def test_bend_allowance_90deg():
    # BA = (π/180) * 90 * (R + K*T)
    # R=2, T=2, K=0.4 → R+K*T = 2.8
    # BA = 1.5708 * 2.8 ≈ 4.398
    ba = bend_allowance(thickness=2.0, bend_radius=2.0, k_factor=0.4, angle_deg=90.0)
    expected = (math.pi / 180.0) * 90.0 * (2.0 + 0.4 * 2.0)
    assert ba == pytest.approx(expected, abs=1e-9)
    assert ba == pytest.approx(4.39822971502571, abs=1e-6)


def test_bend_allowance_invalid_inputs():
    with pytest.raises(ValueError):
        bend_allowance(0, 1.0, 0.4, 90)
    with pytest.raises(ValueError):
        bend_allowance(1.0, -1.0, 0.4, 90)
    with pytest.raises(ValueError):
        bend_allowance(1.0, 1.0, 0.6, 90)
    with pytest.raises(ValueError):
        bend_allowance(1.0, 1.0, 0.4, -10)


def test_default_rules():
    lib = create_default_sheet_metal_rules()
    assert len(lib) >= 3
    steel = lib.get("Mild Steel 1.5mm")
    assert steel is not None
    assert steel["thickness"] == 1.5
    assert steel["k_factor"] == 0.40
    lib.validate()


def test_bend_allowance_zero_angle():
    assert bend_allowance(1.5, 1.5, 0.4, 0.0) == 0.0
