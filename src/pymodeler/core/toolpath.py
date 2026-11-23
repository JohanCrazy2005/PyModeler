"""Early rectangular toolpath / G-code generator.

Pure-Python stub for 2D pocket (concentric or zigzag) and contour operations.
Emits simple G-code (G00/G01/G03, metric absolute). Supports optional linear
lead-in/out and corner-radius arcs (G03 R-format) on rectangular paths.
Validated against schemas/toolpath.schema.json.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_TOOLPATH_SCHEMA_PATH = _SCHEMA_DIR / "toolpath.schema.json"

with open(_TOOLPATH_SCHEMA_PATH, encoding="utf-8") as f:
    TOOLPATH_SCHEMA = json.load(f)

_TOOLPATH_VALIDATOR = Draft202012Validator(TOOLPATH_SCHEMA)


class ToolpathValidationError(ValueError):
    """Raised when toolpath data fails schema validation or cannot be generated."""


def validate_toolpath_data(data: dict) -> None:
    """Validate a dict against the ToolpathJob JSON Schema."""
    errors = sorted(_TOOLPATH_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise ToolpathValidationError(
            "ToolpathJob schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "tp") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _fmt(v: float) -> str:
    """Format a number for G-code (3 decimal places, strip trailing zeros)."""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"


class ToolpathJob:
    """Schema-compliant rectangular toolpath job that can emit G-code."""

    def __init__(
        self,
        operation: str,
        width: float,
        height: float,
        depth: float,
        tool_diameter: float,
        strategy: str = "concentric",
        stepover_fraction: float = 0.5,
        depth_of_cut: float = 1.0,
        feed: float = 500.0,
        plunge_feed: float = 150.0,
        safe_z: float = 5.0,
        spindle_speed: int = 12000,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
        unit: str = "mm",
        name: str = "Toolpath",
        lead_in_length: float = 0.0,
        lead_out_length: float = 0.0,
        corner_radius: float = 0.0,
        id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        if width <= 0 or height <= 0 or depth <= 0 or tool_diameter <= 0:
            raise ToolpathValidationError("Dimensions and tool diameter must be positive")
        if strategy not in ("concentric", "zigzag"):
            raise ToolpathValidationError(f"Unknown strategy: {strategy}")
        if operation not in ("pocket", "contour"):
            raise ToolpathValidationError(f"Unknown operation: {operation}")

        self.id = id or _new_id()
        self.name = name
        self.operation = operation
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.tool_diameter = float(tool_diameter)
        self.strategy = strategy
        self.stepover_fraction = float(stepover_fraction)
        self.depth_of_cut = float(depth_of_cut)
        self.feed = float(feed)
        self.plunge_feed = float(plunge_feed)
        self.safe_z = float(safe_z)
        self.spindle_speed = int(spindle_speed)
        self.origin_x = float(origin_x)
        self.origin_y = float(origin_y)
        self.unit = unit
        self.lead_in_length = float(lead_in_length)
        self.lead_out_length = float(lead_out_length)
        self.corner_radius = float(corner_radius)
        self.gcode: Optional[str] = None
        self.estimated_length: float = 0.0
        self.generated_at: Optional[str] = None
        self.metadata = metadata or {}

        # Early size check for pocket
        if operation == "pocket" and tool_diameter >= min(width, height):
            raise ToolpathValidationError(
                f"Tool diameter {tool_diameter} too large for {width}x{height} pocket"
            )
        self.validate()

    def to_dict(self) -> dict:
        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "operation": self.operation,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "tool_diameter": self.tool_diameter,
            "strategy": self.strategy,
            "stepover_fraction": self.stepover_fraction,
            "depth_of_cut": self.depth_of_cut,
            "feed": self.feed,
            "plunge_feed": self.plunge_feed,
            "safe_z": self.safe_z,
            "spindle_speed": self.spindle_speed,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "unit": self.unit,
            "lead_in_length": self.lead_in_length,
            "lead_out_length": self.lead_out_length,
            "corner_radius": self.corner_radius,
            "estimated_length": self.estimated_length,
        }
        if self.gcode is not None:
            data["gcode"] = self.gcode
        if self.generated_at:
            data["generated_at"] = self.generated_at
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_toolpath_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ToolpathJob":
        validate_toolpath_data(data)
        job = cls(
            operation=data["operation"],
            width=data["width"],
            height=data["height"],
            depth=data["depth"],
            tool_diameter=data["tool_diameter"],
            strategy=data.get("strategy", "concentric"),
            stepover_fraction=data.get("stepover_fraction", 0.5),
            depth_of_cut=data.get("depth_of_cut", 1.0),
            feed=data.get("feed", 500),
            plunge_feed=data.get("plunge_feed", 150),
            safe_z=data.get("safe_z", 5.0),
            spindle_speed=data.get("spindle_speed", 12000),
            origin_x=data.get("origin_x", 0),
            origin_y=data.get("origin_y", 0),
            unit=data.get("unit", "mm"),
            name=data.get("name", "Toolpath"),
            lead_in_length=data.get("lead_in_length", 0.0),
            lead_out_length=data.get("lead_out_length", 0.0),
            corner_radius=data.get("corner_radius", 0.0),
            id=data.get("id"),
            metadata=data.get("metadata"),
        )
        if "gcode" in data:
            job.gcode = data["gcode"]
        job.estimated_length = data.get("estimated_length", 0.0)
        job.generated_at = data.get("generated_at")
        return job

    def generate(self) -> "ToolpathJob":
        """Generate G-code and estimated length. Mutates self."""
        lines: List[str] = []
        length = 0.0

        # Header
        lines.append("(PyModeler toolpath)")
        lines.append(f"(Operation: {self.operation} {self.strategy})")
        lines.append(f"(Size: {self.width}x{self.height} depth {self.depth})")
        lines.append(f"(Tool: {self.tool_diameter} mm)")
        lines.append("G21")  # metric
        lines.append("G90")  # absolute
        lines.append("G17")  # XY plane
        lines.append("G54")
        lines.append(f"S{self.spindle_speed} M03")
        lines.append(f"G00 Z{_fmt(self.safe_z)}")

        radius = self.tool_diameter / 2.0
        stepover = self.tool_diameter * self.stepover_fraction
        n_depths = max(1, math.ceil(self.depth / self.depth_of_cut))
        z_levels = [-(i + 1) * min(self.depth_of_cut, self.depth - i * self.depth_of_cut)
                    for i in range(n_depths)]
        # Ensure last reaches full depth
        z_levels[-1] = -self.depth

        if self.operation == "pocket":
            length += self._generate_pocket(lines, radius, stepover, z_levels)
        else:
            length += self._generate_contour(lines, radius, z_levels)

        # Footer
        lines.append(f"G00 Z{_fmt(self.safe_z)}")
        lines.append("M05")
        lines.append("M30")

        self.gcode = "\n".join(lines) + "\n"
        self.estimated_length = length
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.validate()
        return self

    def _generate_pocket(
        self, lines: List[str], radius: float, stepover: float, z_levels: List[float]
    ) -> float:
        length = 0.0
        # Inner usable area after tool radius
        inner_w = self.width - 2 * radius
        inner_h = self.height - 2 * radius
        if inner_w <= 0 or inner_h <= 0:
            raise ToolpathValidationError("Pocket too small for tool")

        if self.strategy == "zigzag":
            return self._generate_zigzag(lines, radius, stepover, z_levels, inner_w, inner_h)
        # Concentric rectangles
        return self._generate_concentric(lines, radius, stepover, z_levels, inner_w, inner_h)

    def _generate_concentric(
        self, lines: List[str], radius: float, stepover: float, z_levels: List[float],
        inner_w: float, inner_h: float
    ) -> float:
        length = 0.0
        # Build offsets from outside in
        offsets = []
        ox = radius
        oy = radius
        while ox < self.width / 2 and oy < self.height / 2:
            offsets.append((ox, oy))
            ox += stepover
            oy += stepover
            if ox >= self.width / 2 or oy >= self.height / 2:
                break
        if not offsets:
            offsets = [(radius, radius)]

        for z in z_levels:
            for i, (ox, oy) in enumerate(offsets):
                # Rectangle path (tool center)
                x0 = self.origin_x + ox
                y0 = self.origin_y + oy
                x1 = self.origin_x + self.width - ox
                y1 = self.origin_y + self.height - oy
                path = self._rect_path(x0, y0, x1, y1, self.corner_radius)
                length += self._emit_path_with_leads(lines, path, z, is_first=(i == 0))
        return length

    def _generate_zigzag(
        self, lines: List[str], radius: float, stepover: float, z_levels: List[float],
        inner_w: float, inner_h: float
    ) -> float:
        length = 0.0
        y_start = self.origin_y + radius
        y_end = self.origin_y + self.height - radius
        x_left = self.origin_x + radius
        x_right = self.origin_x + self.width - radius
        n_passes = max(1, math.ceil(inner_h / stepover))
        ys = [y_start + i * stepover for i in range(n_passes)]
        if ys[-1] > y_end:
            ys[-1] = y_end

        for z in z_levels:
            direction = 1
            for i, y in enumerate(ys):
                x_from = x_left if direction > 0 else x_right
                x_to = x_right if direction > 0 else x_left
                # Simple linear (zigzag stays linear even with corner_radius)
                path = [(x_from, y), (x_to, y)]
                length += self._emit_path_with_leads(lines, path, z, is_first=(i == 0))
                direction *= -1
                if i < len(ys) - 1:
                    # Linking move
                    next_y = ys[i + 1]
                    lines.append(f"G01 Y{_fmt(next_y)} F{_fmt(self.feed)}")
                    length += abs(next_y - y)
        return length

    def _generate_contour(
        self, lines: List[str], radius: float, z_levels: List[float]
    ) -> float:
        length = 0.0
        # Outside offset for contour (tool outside the feature)
        x0 = self.origin_x - radius
        y0 = self.origin_y - radius
        x1 = self.origin_x + self.width + radius
        y1 = self.origin_y + self.height + radius
        path = self._rect_path(x0, y0, x1, y1, self.corner_radius)
        for z in z_levels:
            length += self._emit_path_with_leads(lines, path, z, is_first=True)
        return length

    def _rect_path(
        self, x0: float, y0: float, x1: float, y1: float, cr: float
    ) -> List[Tuple[float, float, Optional[str]]]:
        """Return list of (x, y, optional_arc_cmd) for a closed rectangle.
        If cr > 0, corners become G03 R-format quarter arcs.
        """
        if cr <= 0:
            return [
                (x0, y0, None),
                (x1, y0, None),
                (x1, y1, None),
                (x0, y1, None),
                (x0, y0, None),
            ]
        # Rounded: straights shortened by cr, then G03 arcs
        # Bottom straight starts after lead-in adjustment
        pts = []
        # Start at bottom-left after radius
        pts.append((x0 + cr, y0, None))
        pts.append((x1 - cr, y0, None))
        pts.append((x1, y0 + cr, "G03 R" + _fmt(cr)))  # arc to right side
        pts.append((x1, y1 - cr, None))
        pts.append((x1 - cr, y1, "G03 R" + _fmt(cr)))
        pts.append((x0 + cr, y1, None))
        pts.append((x0, y1 - cr, "G03 R" + _fmt(cr)))
        pts.append((x0, y0 + cr, None))
        pts.append((x0 + cr, y0, "G03 R" + _fmt(cr)))
        return pts

    def _emit_path_with_leads(
        self, lines: List[str], path: List[Tuple], z: float, is_first: bool
    ) -> float:
        """Emit rapid + lead-in + path + lead-out. Returns length added."""
        length = 0.0
        if not path:
            return 0.0
        start_x, start_y = path[0][0], path[0][1]
        # Lead-in from left
        lead_in = self.lead_in_length if is_first else 0.0
        approach_x = start_x - lead_in
        # Rapid to approach XY at safe Z
        lines.append(f"G00 X{_fmt(approach_x)} Y{_fmt(start_y)}")
        lines.append(f"G00 Z{_fmt(self.safe_z)}")
        # Plunge at approach
        lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
        length += abs(self.safe_z - z)
        # Lead-in to start
        if lead_in > 0:
            lines.append(f"G01 X{_fmt(start_x)} F{_fmt(self.feed)}")
            length += lead_in
        # Path
        prev_x, prev_y = start_x, start_y
        for pt in path[1:]:
            x, y = pt[0], pt[1]
            arc = pt[2] if len(pt) > 2 else None
            if arc:
                lines.append(f"{arc} X{_fmt(x)} Y{_fmt(y)} F{_fmt(self.feed)}")
                # Approximate quarter-arc length
                r = float(arc.split("R")[-1])
                length += 0.5 * math.pi * r
            else:
                lines.append(f"G01 X{_fmt(x)} Y{_fmt(y)} F{_fmt(self.feed)}")
                length += math.hypot(x - prev_x, y - prev_y)
            prev_x, prev_y = x, y
        # Lead-out
        if self.lead_out_length > 0 and is_first:
            lines.append(f"G01 X{_fmt(prev_x + self.lead_out_length)} F{_fmt(self.feed)}")
            length += self.lead_out_length
        # Retract
        lines.append(f"G00 Z{_fmt(self.safe_z)}")
        length += abs(z - self.safe_z)
        return length
