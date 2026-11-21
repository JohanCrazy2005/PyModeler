"""Rectangular nesting job and simple shelf packer.

Early Mozaik-inspired manufacturing helper. Places rectangular parts onto
stock sheets using a pure-Python shelf packing algorithm with optional 90°
rotation. Validated against schemas/nesting_job.schema.json.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_NESTING_SCHEMA_PATH = _SCHEMA_DIR / "nesting_job.schema.json"

with open(_NESTING_SCHEMA_PATH, encoding="utf-8") as f:
    NESTING_JOB_SCHEMA = json.load(f)

_NESTING_VALIDATOR = Draft202012Validator(NESTING_JOB_SCHEMA)


class NestingValidationError(ValueError):
    """Raised when nesting job data fails schema validation or a part cannot be placed."""


def validate_nesting_job_data(data: dict) -> None:
    """Validate a dict against the NestingJob JSON Schema."""
    errors = sorted(_NESTING_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise NestingValidationError(
            "NestingJob schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "nest") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class NestingJob:
    """Schema-compliant rectangular nesting job with shelf packer."""

    def __init__(
        self,
        sheet_width: float,
        sheet_height: float,
        kerf: float = 0.0,
        trim: float = 0.0,
        name: str = "Nesting Job",
        unit: str = "mm",
        parts: Optional[List[dict]] = None,
        id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        if sheet_width <= 0 or sheet_height <= 0:
            raise NestingValidationError("Sheet dimensions must be positive")
        self.id = id or _new_id()
        self.name = name
        self.sheet_width = float(sheet_width)
        self.sheet_height = float(sheet_height)
        self.kerf = float(kerf)
        self.trim = float(trim)
        self.unit = unit
        self.parts: List[dict] = []
        self.layouts: List[dict] = []
        self.sheets_used: int = 0
        self.total_yield: float = 0.0
        self.total_part_area: float = 0.0
        self.generated_at: Optional[str] = None
        self.metadata = metadata or {}
        if parts:
            for p in parts:
                self.add_part(**{k: v for k, v in p.items() if k in ("width", "height", "quantity", "name", "can_rotate", "id", "material", "part_id", "comment")})
        self.validate()

    def add_part(
        self,
        width: float,
        height: float,
        quantity: int = 1,
        name: Optional[str] = None,
        can_rotate: bool = True,
        id: Optional[str] = None,
        material: Optional[str] = None,
        part_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        if width <= 0 or height <= 0 or quantity < 1:
            raise NestingValidationError("Part width/height must be positive and quantity >= 1")
        part = {
            "id": id or _new_id("part"),
            "width": float(width),
            "height": float(height),
            "quantity": int(quantity),
            "can_rotate": bool(can_rotate),
        }
        if name is not None:
            part["name"] = name
        if material is not None:
            part["material"] = material
        if part_id is not None:
            part["part_id"] = part_id
        if comment is not None:
            part["comment"] = comment
        self.parts.append(part)
        self.validate()

    def to_dict(self) -> dict:
        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "sheet_width": self.sheet_width,
            "sheet_height": self.sheet_height,
            "kerf": self.kerf,
            "trim": self.trim,
            "unit": self.unit,
            "parts": list(self.parts),
            "layouts": list(self.layouts),
            "sheets_used": self.sheets_used,
            "total_yield": self.total_yield,
            "total_part_area": self.total_part_area,
        }
        if self.generated_at:
            data["generated_at"] = self.generated_at
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_nesting_job_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "NestingJob":
        validate_nesting_job_data(data)
        job = cls(
            sheet_width=data["sheet_width"],
            sheet_height=data["sheet_height"],
            kerf=data.get("kerf", 0),
            trim=data.get("trim", 0),
            name=data.get("name", "Nesting Job"),
            unit=data.get("unit", "mm"),
            id=data.get("id"),
            metadata=data.get("metadata"),
        )
        # Parts already added via constructor if we pass them, but re-set for exactness
        job.parts = list(data.get("parts", []))
        job.layouts = list(data.get("layouts", []))
        job.sheets_used = data.get("sheets_used", 0)
        job.total_yield = data.get("total_yield", 0.0)
        job.total_part_area = data.get("total_part_area", 0.0)
        job.generated_at = data.get("generated_at")
        job.validate()
        return job

    def pack(self) -> "NestingJob":
        """Run shelf packing. Populates layouts, sheets_used, yields. Raises if a part cannot fit."""
        if not self.parts:
            self.layouts = []
            self.sheets_used = 0
            self.total_yield = 0.0
            self.total_part_area = 0.0
            self.generated_at = datetime.now(timezone.utc).isoformat()
            self.validate()
            return self

        # Expand into individual instances
        items: List[dict] = []
        for part in self.parts:
            for q_idx in range(part["quantity"]):
                items.append({
                    "width": part["width"],
                    "height": part["height"],
                    "can_rotate": part.get("can_rotate", True),
                    "part_id": part.get("id"),
                    "name": part.get("name"),
                    "quantity_index": q_idx,
                    "original": part,
                })

        # Sort by max dimension descending for better packing
        items.sort(key=lambda it: max(it["width"], it["height"]), reverse=True)

        sheets: List[dict] = []  # each: {"placements": [], "shelves": [...]}

        def new_sheet() -> dict:
            return {
                "placements": [],
                "current_y": 0.0,
                "current_x": 0.0,
                "shelf_height": 0.0,
            }

        current = new_sheet()
        sheets.append(current)

        for item in items:
            placed = False
            # Try both orientations
            orientations = [(item["width"], item["height"], False)]
            if item["can_rotate"] and abs(item["width"] - item["height"]) > 1e-6:
                orientations.append((item["height"], item["width"], True))

            for w, h, rotated in orientations:
                if w > self.sheet_width + 1e-6 or h > self.sheet_height + 1e-6:
                    continue
                # Try to place on current sheet
                if _try_place(current, w, h, self.sheet_width, self.sheet_height, self.kerf):
                    placement = {
                        "x": current["_last_x"],
                        "y": current["_last_y"],
                        "width": w,
                        "height": h,
                        "rotated": rotated,
                        "part_id": item["part_id"],
                        "quantity_index": item["quantity_index"],
                    }
                    if item["name"]:
                        placement["name"] = item["name"]
                    current["placements"].append(placement)
                    placed = True
                    break

            if not placed:
                # Start a new sheet and retry
                current = new_sheet()
                sheets.append(current)
                for w, h, rotated in orientations:
                    if w > self.sheet_width + 1e-6 or h > self.sheet_height + 1e-6:
                        continue
                    if _try_place(current, w, h, self.sheet_width, self.sheet_height, self.kerf):
                        placement = {
                            "x": current["_last_x"],
                            "y": current["_last_y"],
                            "width": w,
                            "height": h,
                            "rotated": rotated,
                            "part_id": item["part_id"],
                            "quantity_index": item["quantity_index"],
                        }
                        if item["name"]:
                            placement["name"] = item["name"]
                        current["placements"].append(placement)
                        placed = True
                        break
                if not placed:
                    raise NestingValidationError(
                        f"Part {item.get('name') or item['part_id']} ({item['width']}x{item['height']}) "
                        f"cannot fit on a {self.sheet_width}x{self.sheet_height} sheet"
                    )

        # Build layouts and compute yields
        self.layouts = []
        total_part_area = 0.0
        sheet_area = self.sheet_width * self.sheet_height
        for idx, sheet in enumerate(sheets):
            placements = sheet["placements"]
            used = sum(p["width"] * p["height"] for p in placements)
            total_part_area += used
            yld = used / sheet_area if sheet_area > 0 else 0.0
            self.layouts.append({
                "sheet_index": idx,
                "placements": placements,
                "used_area": used,
                "yield": yld,
            })

        self.sheets_used = len(sheets)
        self.total_part_area = total_part_area
        total_sheet_area = self.sheets_used * sheet_area
        self.total_yield = total_part_area / total_sheet_area if total_sheet_area > 0 else 0.0
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.validate()
        return self

    def summary(self) -> str:
        lines = [
            f"Nesting Job: {self.name}",
            f"Sheet size: {self.sheet_width} x {self.sheet_height} {self.unit}",
            f"Kerf: {self.kerf}",
            f"Sheets used: {self.sheets_used}",
            f"Total part area: {self.total_part_area:.1f}",
            f"Overall yield: {self.total_yield * 100:.1f}%",
            "",
        ]
        for layout in self.layouts:
            lines.append(
                f"Sheet {layout['sheet_index'] + 1}: "
                f"{len(layout['placements'])} parts, "
                f"yield {layout['yield'] * 100:.1f}%"
            )
        return "\n".join(lines)


def _try_place(
    sheet: dict,
    w: float,
    h: float,
    sheet_w: float,
    sheet_h: float,
    kerf: float,
) -> bool:
    """Try to place a rectangle on the current shelf or open a new one. Mutates sheet state."""
    # Prefer current shelf if it fits in remaining x and height
    if (
        sheet["current_x"] + w <= sheet_w + 1e-6
        and sheet["current_y"] + h <= sheet_h + 1e-6
    ):
        sheet["_last_x"] = sheet["current_x"]
        sheet["_last_y"] = sheet["current_y"]
        sheet["current_x"] += w + kerf
        sheet["shelf_height"] = max(sheet["shelf_height"], h)
        return True

    # Open a new shelf
    new_y = sheet["current_y"] + sheet["shelf_height"] + kerf
    if new_y + h <= sheet_h + 1e-6 and w <= sheet_w + 1e-6:
        sheet["current_y"] = new_y
        sheet["current_x"] = 0.0
        sheet["shelf_height"] = h
        sheet["_last_x"] = 0.0
        sheet["_last_y"] = new_y
        sheet["current_x"] = w + kerf
        return True

    return False


def nesting_job_from_cutlist(
    cutlist: dict,
    sheet_width: float,
    sheet_height: float,
    kerf: float = 0.0,
    trim: float = 0.0,
    name: Optional[str] = None,
) -> NestingJob:
    """Create a NestingJob from a CutList dict, using width × depth as the 2D blank."""
    job = NestingJob(
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        kerf=kerf,
        trim=trim,
        name=name or cutlist.get("name", "From CutList"),
    )
    for item in cutlist.get("items", []):
        size = item.get("size") or {}
        width = size.get("width")
        height = size.get("depth") or size.get("height")  # depth is the other planar dim
        if width is None or height is None:
            continue
        job.add_part(
            width=width,
            height=height,
            quantity=item.get("quantity", 1),
            name=item.get("name"),
            material=item.get("material_name"),
            part_id=item.get("part_id"),
            can_rotate=True,
        )
    return job
