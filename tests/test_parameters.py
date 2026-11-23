"""Tests for the ParameterStore."""

import pytest

from pymodeler.core.parameters import (
    ParameterStore,
    ParameterValidationError,
    ParameterEvaluationError,
    validate_parameter_data,
)


def test_empty_store():
    store = ParameterStore(name="Empty")
    assert store.name == "Empty"
    assert len(store.parameters) == 0
    store.validate()


def test_add_numeric_and_evaluate():
    store = ParameterStore()
    store.add("Width", value=100.0, unit="mm")
    store.add("Height", value=50.0)
    assert store.evaluate("Width") == 100.0
    assert store.evaluate("Height") == 50.0
    assert "Width" in store.names()


def test_expression_with_named_reference():
    store = ParameterStore()
    store.add("Width", value=10.0)
    store.add("Height", expression="Width * 2")
    store.add("Area", expression="Width * Height")
    assert store.evaluate("Height") == 20.0
    assert store.evaluate("Area") == 200.0


def test_update_propagates():
    store = ParameterStore()
    store.add("Base", value=5.0)
    store.add("Double", expression="Base * 2")
    assert store.evaluate("Double") == 10.0
    store.update("Base", value=7.0)
    assert store.evaluate("Double") == 14.0


def test_roundtrip_schema():
    store = ParameterStore(name="Test")
    store.add("A", value=1.5, comment="first")
    store.add("B", expression="A + 3", unit="mm")
    data = store.to_dict()
    validate_parameter_data(data)
    restored = ParameterStore.from_dict(data)
    assert restored.name == store.name
    assert len(restored.parameters) == 2
    assert restored.evaluate("B") == 4.5


def test_circular_reference_detected():
    store = ParameterStore()
    store.add("A", expression="B")
    store.add("B", expression="A")
    with pytest.raises(ParameterEvaluationError):
        store.evaluate("A")


def test_unknown_parameter():
    store = ParameterStore()
    with pytest.raises(ParameterEvaluationError):
        store.evaluate("Missing")


def test_evaluate_expression_free_form():
    store = ParameterStore()
    store.add("width", value=10.0)
    store.add("offset", value=2.5)
    assert store.evaluate_expression("width * 2 + offset") == 22.5
    assert store.evaluate_expression("(width + 1) / 2") == 5.5
    assert store.evaluate_expression("-width") == -10.0
    with pytest.raises(ParameterEvaluationError):
        store.evaluate_expression("unknown * 2")
    with pytest.raises(ParameterEvaluationError):
        store.evaluate_expression("width +")


def test_evaluate_expression_math_functions_and_units():
    store = ParameterStore()
    store.add("angle", value=30.0)
    store.add("length_in", value=2.0)
    # trig in degrees (CAD convention)
    assert abs(store.evaluate_expression("sin(angle)") - 0.5) < 1e-6
    assert abs(store.evaluate_expression("cos(60)") - 0.5) < 1e-6
    assert abs(store.evaluate_expression("sqrt(4)") - 2.0) < 1e-9
    assert store.evaluate_expression("abs(-5)") == 5.0
    assert store.evaluate_expression("max(1, 3, 2)") == 3.0
    assert store.evaluate_expression("min(1, 3, 2)") == 1.0
    # power
    assert store.evaluate_expression("2 ** 3") == 8.0
    # constants
    assert abs(store.evaluate_expression("pi") - 3.141592653589793) < 1e-9
    # unit helpers still work
    assert abs(store.evaluate_expression("in_to_mm(length_in)") - 50.8) < 1e-9


def test_unit_suffixes_in_expressions():
    store = ParameterStore()
    store.add("width", expression="2 in + 10 mm")
    store.add("height", expression="1.5ft")
    store.add("mixed", expression="10cm + 0.5 m")
    assert abs(store.evaluate("width") - (2 * 25.4 + 10)) < 1e-6
    assert abs(store.evaluate("height") - 1.5 * 304.8) < 1e-6
    assert abs(store.evaluate("mixed") - (10 * 10 + 0.5 * 1000)) < 1e-6
    # free-form
    assert abs(store.evaluate_expression("2in + 10mm") - (50.8 + 10)) < 1e-6
    assert abs(store.evaluate_expression("1 ft") - 304.8) < 1e-6
    # bare numbers still work
    assert store.evaluate_expression("10 + 2") == 12.0
    # existing functions unaffected
    assert abs(store.evaluate_expression("in_to_mm(2)") - 50.8) < 1e-9
    # unit helpers
    assert abs(store.evaluate_expression("mm_to_in(25.4)") - 1.0) < 1e-9
    # radians versions
    assert abs(store.evaluate_expression("sin_rad(pi / 2)") - 1.0) < 1e-6
    # unknown function
    with pytest.raises(ParameterEvaluationError):
        store.evaluate_expression("unknown_func(1)")
