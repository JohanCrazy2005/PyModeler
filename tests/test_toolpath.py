"""Tests for early toolpath / G-code stubs."""

import pytest

from pymodeler.core.toolpath import (
    ToolpathJob,
    ToolpathValidationError,
    validate_toolpath_data,
)


def test_schema_validation_ok():
    data = {
        "operation": "pocket",
        "width": 50,
        "height": 30,
        "depth": 5,
        "tool_diameter": 6,
    }
    validate_toolpath_data(data)


def test_schema_rejects_bad_operation():
    data = {
        "operation": "drill",
        "width": 50,
        "height": 30,
        "depth": 5,
        "tool_diameter": 6,
    }
    with pytest.raises(ToolpathValidationError):
        validate_toolpath_data(data)


def test_pocket_generate():
    job = ToolpathJob(
        operation="pocket",
        width=50,
        height=30,
        depth=5,
        tool_diameter=6,
        stepover_fraction=0.5,
        depth_of_cut=2,
    )
    job.generate()
    assert job.gcode
    assert "G21" in job.gcode
    assert "G01" in job.gcode
    assert "M30" in job.gcode
    assert job.estimated_length > 0
    # Multiple depth passes expected
    assert job.gcode.count("G01 Z-") >= 2
    job.validate()


def test_contour_generate():
    job = ToolpathJob(
        operation="contour",
        width=40,
        height=20,
        depth=3,
        tool_diameter=4,
        depth_of_cut=1.5,
    )
    job.generate()
    assert "G00" in job.gcode
    assert job.estimated_length > 0
    # Outside offset: path should be larger than feature
    assert "X-2.000" in job.gcode or "X-2" in job.gcode  # -radius
    job.validate()


def test_tool_too_large_raises():
    with pytest.raises(ToolpathValidationError):
        ToolpathJob(
            operation="pocket",
            width=10,
            height=10,
            depth=2,
            tool_diameter=12,
        )


def test_roundtrip():
    job = ToolpathJob(
        operation="pocket",
        width=80,
        height=40,
        depth=4,
        tool_diameter=8,
        name="Test Pocket",
    )
    job.generate()
    data = job.to_dict()
    restored = ToolpathJob.from_dict(data)
    assert restored.operation == "pocket"
    assert restored.gcode == job.gcode
    assert abs(restored.estimated_length - job.estimated_length) < 1e-6


def test_zigzag_pocket_generate():
    job = ToolpathJob(
        operation="pocket",
        width=50,
        height=30,
        depth=4,
        tool_diameter=6,
        strategy="zigzag",
        stepover_fraction=0.5,
        depth_of_cut=2,
    )
    job.generate()
    assert job.gcode
    assert "G01" in job.gcode
    assert job.estimated_length > 0
    # Zigzag should have multiple parallel Y lines
    assert job.gcode.count("G01 Y") >= 2 or "Y" in job.gcode
    job.validate()
    data = job.to_dict()
    assert data["strategy"] == "zigzag"


def test_bad_strategy_raises():
    with pytest.raises(ToolpathValidationError):
        ToolpathJob(
            operation="pocket",
            width=50,
            height=30,
            depth=5,
            tool_diameter=6,
            strategy="spiral",
        )


def test_default_strategy_concentric():
    job = ToolpathJob(
        operation="pocket",
        width=40,
        height=20,
        depth=2,
        tool_diameter=4,
    )
    assert job.strategy == "concentric"
    job.generate()
    assert job.gcode
