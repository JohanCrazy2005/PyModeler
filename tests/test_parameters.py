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
