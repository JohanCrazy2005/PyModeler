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

DEFAULT_SHEET_SIZES = [
    {"name": "half", "width": 1220.0, "height": 1220.0},
    {"name": "full", "width": 2440.0, "height": 1220.0},
    {"name": "square", "width": 1220.0, "height": 1220.0},
]


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
        sheet_sizes: Optional[List[dict]] = None,
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
        self.sheet_sizes: List[dict] = list(sheet_sizes or [])
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
        if self.sheet_sizes:
            data["sheet_sizes"] = list(self.sheet_sizes)
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
            sheet_sizes=data.get("sheet_sizes"),
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

        sheets: List[dict] = []  # each: {"placements": [], "shelves": [...], "sheet_w", "sheet_h", "sheet_name"}

        def _choose_sheet_for(item: dict) -> tuple[float, float, Optional[str]]:
            """Return (width, height, name) of the smallest available sheet that can fit the item (or primary)."""
            candidates = []
            # Primary always available
            candidates.append((self.sheet_width, self.sheet_height, None))
            for sz in self.sheet_sizes:
                candidates.append((sz["width"], sz["height"], sz.get("name")))
            # Prefer smallest area that fits both orientations
            best = None
            best_area = float("inf")
            for w, h, name in candidates:
                fits = False
                for ow, oh in [(item["width"], item["height"]), (item["height"], item["width"])]:
                    if ow <= w + 1e-6 and oh <= h + 1e-6:
                        fits = True
                        break
                if fits:
                    area = w * h
                    if area < best_area:
                        best_area = area
                        best = (w, h, name)
            if best:
                return best
            # Fallback to primary even if it doesn't fit (will raise later)
            return self.sheet_width, self.sheet_height, None

        def new_sheet(item: Optional[dict] = None) -> dict:
            if item is not None:
                sw, sh, sname = _choose_sheet_for(item)
            else:
                sw, sh, sname = self.sheet_width, self.sheet_height, None
            return {
                "placements": [],
                "current_y": 0.0,
                "current_x": 0.0,
                "shelf_height": 0.0,
                "sheet_w": sw,
                "sheet_h": sh,
                "sheet_name": sname,
            }

        current = None
        sheets: List[dict] = []

        for item in items:
            placed = False
            # Try both orientations
            orientations = [(item["width"], item["height"], False)]
            if item["can_rotate"] and abs(item["width"] - item["height"]) > 1e-6:
                orientations.append((item["height"], item["width"], True))

            # Prefer current sheet if it exists
            if current is not None:
                for w, h, rotated in orientations:
                    if w > current["sheet_w"] + 1e-6 or h > current["sheet_h"] + 1e-6:
                        continue
                    if _try_place(current, w, h, current["sheet_w"], current["sheet_h"], self.kerf):
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
                # Start a new sheet chosen for this item
                current = new_sheet(item)
                sheets.append(current)
                for w, h, rotated in orientations:
                    if w > current["sheet_w"] + 1e-6 or h > current["sheet_h"] + 1e-6:
                        continue
                    if _try_place(current, w, h, current["sheet_w"], current["sheet_h"], self.kerf):
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
                        f"cannot fit on any available sheet"
                    )

        # Build layouts and compute yields
        self.layouts = []
        total_part_area = 0.0
        for idx, sheet in enumerate(sheets):
            placements = sheet["placements"]
            used = sum(p["width"] * p["height"] for p in placements)
            total_part_area += used
            sw = sheet["sheet_w"]
            sh = sheet["sheet_h"]
            sheet_area = sw * sh
            yld = used / sheet_area if sheet_area > 0 else 0.0
            remnant = sheet_area - used
            layout = {
                "sheet_index": idx,
                "placements": placements,
                "used_area": used,
                "yield": yld,
                "remnant_area": remnant,
                "sheet_width": sw,
                "sheet_height": sh,
            }
            if sheet.get("sheet_name"):
                layout["sheet_name"] = sheet["sheet_name"]
            self.layouts.append(layout)

        self.sheets_used = len(sheets)
        self.total_part_area = total_part_area
        total_sheet_area = sum(s["sheet_w"] * s["sheet_h"] for s in sheets)
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
            sz = f"{layout.get('sheet_width', self.sheet_width)}x{layout.get('sheet_height', self.sheet_height)}"
            name = f" ({layout['sheet_name']})" if layout.get("sheet_name") else ""
            lines.append(
                f"Sheet {layout['sheet_index'] + 1}{name} [{sz}]: "
                f"{len(layout['placements'])} parts, "
                f"yield {layout['yield'] * 100:.1f}%, "
                f"remnant {layout.get('remnant_area', 0):.0f}"
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


def nesting_job_from_parts(
    parts: list,
    sheet_width: float = 2440.0,
    sheet_height: float = 1220.0,
    kerf: float = 3.0,
    name: str = "Nesting from Parts",
    material_store=None,
    use_fallback_sample: bool = True,
) -> NestingJob:
    """Convenience: generate cut list from Parts then build a NestingJob.

    Returns an unpacked NestingJob (caller should call .pack()).
    Parts without a bounding-box size are skipped.
    If no usable parts and use_fallback_sample=True, returns a small demo job
    so the UI always has something to show.
    """
    from .cutlist import generate_cut_list  # local import to avoid cycles

    cutlist = generate_cut_list(parts, material_store=material_store, name=name)
    job = nesting_job_from_cutlist(
        cutlist,
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        kerf=kerf,
        name=name,
    )
    job.sheet_sizes = list(DEFAULT_SHEET_SIZES)
    if not job.parts and use_fallback_sample:
        job = NestingJob(
            sheet_width=sheet_width,
            sheet_height=sheet_height,
            kerf=kerf,
            name=name + " (sample)",
            sheet_sizes=list(DEFAULT_SHEET_SIZES),
        )
        job.add_part(width=400, height=300, quantity=2, name="Sample A")
        job.add_part(width=200, height=150, quantity=3, name="Sample B")
    return job
