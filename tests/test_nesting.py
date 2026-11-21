"""Tests for NestingJob rectangular packer stub."""

import pytest

from pymodeler.core.nesting import (
    NestingJob,
    NestingValidationError,
    nesting_job_from_cutlist,
    validate_nesting_job_data,
)


def test_schema_validation_minimal():
    job = NestingJob(sheet_width=2440, sheet_height=1220)
    job.add_part(600, 400, quantity=2, name="panel")
    data = job.to_dict()
    validate_nesting_job_data(data)
    assert data["sheet_width"] == 2440
    assert len(data["parts"]) == 1
    assert data["parts"][0]["quantity"] == 2


def test_pack_single_sheet():
    job = NestingJob(sheet_width=1000, sheet_height=500, kerf=2.0)
    job.add_part(300, 200, quantity=2, name="A")
    job.add_part(200, 150, quantity=1, name="B")
    result = job.pack()
    assert job.sheets_used == 1
    assert len(job.layouts) == 1
    assert len(job.layouts[0]["placements"]) == 3
    assert 0 < job.total_yield <= 1.0
    # No overlaps (simple check)
    placements = job.layouts[0]["placements"]
    for i, p1 in enumerate(placements):
        for p2 in placements[i + 1 :]:
            # Axis-aligned overlap test
            if (
                p1["x"] < p2["x"] + p2["width"]
                and p1["x"] + p1["width"] > p2["x"]
                and p1["y"] < p2["y"] + p2["height"]
                and p1["y"] + p1["height"] > p2["y"]
            ):
                pytest.fail(f"Overlap detected between {p1} and {p2}")


def test_pack_needs_two_sheets():
    job = NestingJob(sheet_width=500, sheet_height=500, kerf=0)
    job.add_part(400, 400, quantity=2, name="large")
    job.pack()
    assert job.sheets_used == 2
    assert job.total_yield > 0.5


def test_rotation_helps():
    # Part that only fits when rotated (250x150 on 200x300 sheet)
    job = NestingJob(sheet_width=200, sheet_height=300, kerf=0)
    job.add_part(250, 150, quantity=1, name="tall", can_rotate=True)
    job.pack()
    assert job.sheets_used == 1
    placement = job.layouts[0]["placements"][0]
    assert placement["rotated"] is True
    assert placement["width"] == 150  # rotated
    assert placement["height"] == 250


def test_cannot_fit_raises():
    job = NestingJob(sheet_width=100, sheet_height=100)
    job.add_part(200, 50, quantity=1, can_rotate=True)
    with pytest.raises(NestingValidationError):
        job.pack()


def test_from_cutlist():
    cutlist = {
        "id": "cl_test",
        "name": "Test",
        "items": [
            {
                "part_id": "p1",
                "name": "Shelf",
                "quantity": 2,
                "material_name": "Birch",
                "size": {"width": 600, "depth": 300, "height": 18},
            }
        ],
    }
    job = nesting_job_from_cutlist(cutlist, sheet_width=2440, sheet_height=1220, kerf=3)
    assert len(job.parts) == 1
    assert job.parts[0]["quantity"] == 2
    assert job.parts[0]["width"] == 600
    job.pack()
    assert job.sheets_used >= 1
    assert job.total_yield > 0


def test_summary():
    job = NestingJob(sheet_width=1000, sheet_height=500)
    job.add_part(200, 100, quantity=1)
    job.pack()
    text = job.summary()
    assert "Sheets used" in text
    assert "yield" in text.lower()
