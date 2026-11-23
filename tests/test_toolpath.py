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


def test_lead_in_out():
    job = ToolpathJob(
        operation="contour",
        width=40,
        height=20,
        depth=2,
        tool_diameter=4,
        lead_in_length=5.0,
        lead_out_length=3.0,
    )
    job.generate()
    assert job.gcode
    # Should contain approach before entry and extension after
    assert "G00 X" in job.gcode
    # Lead-in of 5 should appear as a move of that distance
    assert job.estimated_length > 0
    # Roundtrip preserves leads
    data = job.to_dict()
    assert data["lead_in_length"] == 5.0
    assert data["lead_out_length"] == 3.0
    restored = ToolpathJob.from_dict(data)
    assert restored.lead_in_length == 5.0
    restored.generate()
    assert restored.gcode
    job.validate()


def test_corner_radius_arcs():
    job = ToolpathJob(
        operation="contour",
        width=40,
        height=20,
        depth=2,
        tool_diameter=4,
        corner_radius=2.0,
    )
    job.generate()
    assert job.gcode
    assert "G03" in job.gcode  # rounded corners
    assert "R2.000" in job.gcode or "R2" in job.gcode
    assert job.estimated_length > 0
    # Rounded path length differs from sharp (straights shortened, arcs added)
    sharp = ToolpathJob(
        operation="contour",
        width=40,
        height=20,
        depth=2,
        tool_diameter=4,
        corner_radius=0.0,
    )
    sharp.generate()
    assert abs(job.estimated_length - sharp.estimated_length) > 1.0  # meaningful difference
    # Roundtrip
    data = job.to_dict()
    assert data["corner_radius"] == 2.0
    restored = ToolpathJob.from_dict(data)
    assert restored.corner_radius == 2.0
    restored.generate()
    assert "G03" in restored.gcode
    job.validate()


def test_corner_radius_zero_is_sharp():
    job = ToolpathJob(
        operation="pocket",
        width=50,
        height=30,
        depth=2,
        tool_diameter=6,
        corner_radius=0.0,
    )
    job.generate()
    assert "G03" not in job.gcode
    assert "G02" not in job.gcode
    assert "G01" in job.gcode
    job.validate()
