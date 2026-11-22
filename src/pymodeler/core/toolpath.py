"""Early toolpath / G-code generation stubs.

Pure-Python rectangular pocket and contour generators that emit simple G-code.
Validated against schemas/toolpath.schema.json. No geometry kernel required.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_TOOLPATH_SCHEMA_PATH = _SCHEMA_DIR / "toolpath.schema.json"

with open(_TOOLPATH_SCHEMA_PATH, encoding="utf-8") as f:
    TOOLPATH_SCHEMA = json.load(f)

_TOOLPATH_VALIDATOR = Draft202012Validator(TOOLPATH_SCHEMA)


class ToolpathValidationError(ValueError):
    """Raised when toolpath data fails schema validation or generation is impossible."""


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


class ToolpathJob:
    """Schema-compliant simple 2D toolpath that can generate G-code."""

    def __init__(
        self,
        operation: str,
        width: float,
        height: float,
        depth: float,
        tool_diameter: float,
        name: str = "Toolpath",
        stepover_fraction: float = 0.5,
        depth_of_cut: float = 1.0,
        feed: float = 500.0,
        plunge_feed: float = 150.0,
        safe_z: float = 5.0,
        spindle_speed: int = 12000,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
        unit: str = "mm",
        strategy: str = "concentric",
        id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        if operation not in ("pocket", "contour"):
            raise ToolpathValidationError("operation must be 'pocket' or 'contour'")
        if strategy not in ("concentric", "zigzag"):
            raise ToolpathValidationError("strategy must be 'concentric' or 'zigzag'")
        if width <= 0 or height <= 0 or depth <= 0 or tool_diameter <= 0:
            raise ToolpathValidationError("Dimensions and tool diameter must be positive")
        if tool_diameter >= min(width, height):
            raise ToolpathValidationError("Tool diameter must be smaller than the feature")

        self.id = id or _new_id()
        self.name = name
        self.operation = operation
        self.strategy = strategy
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.tool_diameter = float(tool_diameter)
        self.stepover_fraction = float(stepover_fraction)
        self.depth_of_cut = float(depth_of_cut)
        self.feed = float(feed)
        self.plunge_feed = float(plunge_feed)
        self.safe_z = float(safe_z)
        self.spindle_speed = int(spindle_speed)
        self.origin_x = float(origin_x)
        self.origin_y = float(origin_y)
        self.unit = unit
        self.gcode: str = ""
        self.estimated_length: float = 0.0
        self.generated_at: Optional[str] = None
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "operation": self.operation,
            "strategy": self.strategy,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "tool_diameter": self.tool_diameter,
            "stepover_fraction": self.stepover_fraction,
            "depth_of_cut": self.depth_of_cut,
            "feed": self.feed,
            "plunge_feed": self.plunge_feed,
            "safe_z": self.safe_z,
            "spindle_speed": self.spindle_speed,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "unit": self.unit,
            "gcode": self.gcode,
            "estimated_length": self.estimated_length,
        }
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
            name=data.get("name", "Toolpath"),
            stepover_fraction=data.get("stepover_fraction", 0.5),
            depth_of_cut=data.get("depth_of_cut", 1.0),
            feed=data.get("feed", 500),
            plunge_feed=data.get("plunge_feed", 150),
            safe_z=data.get("safe_z", 5.0),
            spindle_speed=data.get("spindle_speed", 12000),
            origin_x=data.get("origin_x", 0.0),
            origin_y=data.get("origin_y", 0.0),
            unit=data.get("unit", "mm"),
            strategy=data.get("strategy", "concentric"),
            id=data.get("id"),
            metadata=data.get("metadata"),
        )
        job.gcode = data.get("gcode", "")
        job.estimated_length = data.get("estimated_length", 0.0)
        job.generated_at = data.get("generated_at")
        job.validate()
        return job

    def generate(self) -> "ToolpathJob":
        """Generate G-code for the configured operation. Populates gcode and estimated_length."""
        lines: List[str] = []
        # Header
        lines.append(f"(PyModeler {self.operation} {self.name})")
        lines.append(f"G21 G90 G17 G40 G49 G80")  # metric, absolute, XY, cancel comp/cycles
        lines.append(f"G54")
        lines.append(f"S{self.spindle_speed} M03")
        lines.append(f"G00 Z{self.safe_z:.3f}")

        radius = self.tool_diameter / 2.0
        stepover = self.tool_diameter * self.stepover_fraction
        # Depth passes
        n_passes = max(1, math.ceil(self.depth / self.depth_of_cut))
        z_levels = []
        for i in range(1, n_passes + 1):
            z = -min(i * self.depth_of_cut, self.depth)
            z_levels.append(z)

        total_length = 0.0

        if self.operation == "pocket":
            if self.strategy == "zigzag":
                total_length = self._generate_zigzag_pocket(lines, radius, stepover, z_levels)
            else:
                total_length = self._generate_pocket(lines, radius, stepover, z_levels)
        else:
            total_length = self._generate_contour(lines, radius, z_levels)

        # Footer
        lines.append(f"G00 Z{self.safe_z:.3f}")
        lines.append("M05")
        lines.append("M30")

        self.gcode = "\n".join(lines) + "\n"
        self.estimated_length = total_length
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.validate()
        return self

    def _generate_pocket(
        self, lines: List[str], radius: float, stepover: float, z_levels: List[float]
    ) -> float:
        """Concentric rectangular pocket, starting from outer safe offset and stepping inward."""
        # Effective cutting area after tool radius
        inner_w = self.width - 2 * radius
        inner_h = self.height - 2 * radius
        if inner_w <= 0 or inner_h <= 0:
            raise ToolpathValidationError("Feature too small for tool diameter")

        total = 0.0
        # Start from largest inset that still fits, step inward
        # First offset is radius from wall, then stepover each time
        max_inset = min(inner_w, inner_h) / 2.0
        insets = []
        inset = radius
        while inset < max_inset + 1e-6:
            insets.append(inset)
            inset += stepover
        if not insets:
            insets = [radius]

        # Reverse so we start near center and spiral out (common for better chip clearance)
        # or keep outer-to-inner; outer-to-inner is fine for stub
        insets = list(reversed(insets))

        for z in z_levels:
            for inset in insets:
                w = self.width - 2 * inset
                h = self.height - 2 * inset
                if w <= 0 or h <= 0:
                    continue
                # Rectangle path starting at bottom-left of the offset rect
                x0 = self.origin_x + inset
                y0 = self.origin_y + inset
                x1 = x0 + w
                y1 = y0 + h
                # Rapid to start at safe, then plunge
                lines.append(f"G00 X{x0:.3f} Y{y0:.3f}")
                lines.append(f"G01 Z{z:.3f} F{self.plunge_feed:.0f}")
                # Trace rectangle
                path = [
                    (x1, y0),
                    (x1, y1),
                    (x0, y1),
                    (x0, y0),
                ]
                prev = (x0, y0)
                for px, py in path:
                    lines.append(f"G01 X{px:.3f} Y{py:.3f} F{self.feed:.0f}")
                    total += math.hypot(px - prev[0], py - prev[1])
                    prev = (px, py)
                # Retract slightly between passes if desired; for stub stay at depth until next
        return total

    def _generate_zigzag_pocket(
        self, lines: List[str], radius: float, stepover: float, z_levels: List[float]
    ) -> float:
        """Simple zig-zag (raster) pocket along X, stepping in Y."""
        # Effective area
        x_min = self.origin_x + radius
        x_max = self.origin_x + self.width - radius
        y_min = self.origin_y + radius
        y_max = self.origin_y + self.height - radius
        if x_max <= x_min or y_max <= y_min:
            raise ToolpathValidationError("Feature too small for tool diameter")

        total = 0.0
        # Y steps
        y_steps = []
        y = y_min
        direction = 1
        while y <= y_max + 1e-6:
            y_steps.append(y)
            y += stepover
        if y_steps[-1] < y_max - 1e-6:
            y_steps.append(y_max)

        for z in z_levels:
            lines.append(f"G00 X{x_min:.3f} Y{y_steps[0]:.3f}")
            lines.append(f"G01 Z{z:.3f} F{self.plunge_feed:.0f}")
            prev = (x_min, y_steps[0])
            for i, y in enumerate(y_steps):
                if direction > 0:
                    target = (x_max, y)
                else:
                    target = (x_min, y)
                lines.append(f"G01 X{target[0]:.3f} Y{target[1]:.3f} F{self.feed:.0f}")
                total += math.hypot(target[0] - prev[0], target[1] - prev[1])
                prev = target
                direction = -direction
                # short step to next Y if not last
                if i + 1 < len(y_steps):
                    next_y = y_steps[i + 1]
                    lines.append(f"G01 X{prev[0]:.3f} Y{next_y:.3f} F{self.feed:.0f}")
                    total += abs(next_y - prev[1])
                    prev = (prev[0], next_y)
        return total

    def _generate_contour(
        self, lines: List[str], radius: float, z_levels: List[float]
    ) -> float:
        """Outside contour: tool center offset outward by radius."""
        # Offset outward
        x0 = self.origin_x - radius
        y0 = self.origin_y - radius
        x1 = self.origin_x + self.width + radius
        y1 = self.origin_y + self.height + radius

        total = 0.0
        for z in z_levels:
            lines.append(f"G00 X{x0:.3f} Y{y0:.3f}")
            lines.append(f"G01 Z{z:.3f} F{self.plunge_feed:.0f}")
            path = [(x1, y0), (x1, y1), (x0, y1), (x0, y0)]
            prev = (x0, y0)
            for px, py in path:
                lines.append(f"G01 X{px:.3f} Y{py:.3f} F{self.feed:.0f}")
                total += math.hypot(px - prev[0], py - prev[1])
                prev = (px, py)
        return total

    def summary(self) -> str:
        return (
            f"Toolpath {self.name} ({self.operation}/{self.strategy})\n"
            f"Size: {self.width} x {self.height} x {self.depth} {self.unit}\n"
            f"Tool: Ø{self.tool_diameter}  stepover={self.stepover_fraction:.0%}\n"
            f"Estimated cut length: {self.estimated_length:.1f}\n"
            f"G-code lines: {len(self.gcode.splitlines()) if self.gcode else 0}"
        )
