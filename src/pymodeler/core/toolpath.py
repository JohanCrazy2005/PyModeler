"""Early rectangular toolpath / G-code generator.

Pure-Python stub for 2D pocket (concentric, zigzag, or spiral) and contour operations.
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


def parse_gcode_paths(gcode: str) -> List[List[Tuple[float, float]]]:
    """Extract continuous XY path segments from G-code.

    Rapid (G00) starts a new segment; feed moves (G01/G03) continue the current one.
    Arcs are approximated as straight lines between endpoints for preview.
    Pure function, no UI dependency.
    """
    import re
    gcode_xy = re.compile(r"([XY])([-+]?\d*\.?\d+)", re.IGNORECASE)
    segments: List[List[Tuple[float, float]]] = []
    current: List[Tuple[float, float]] = []
    x = 0.0
    y = 0.0
    for raw in gcode.splitlines():
        line = raw.strip()
        if not line or line.startswith("("):
            continue
        upper = line.upper()
        found = {m.group(1).upper(): float(m.group(2)) for m in gcode_xy.finditer(line)}
        if "X" in found:
            x = found["X"]
        if "Y" in found:
            y = found["Y"]
        if upper.startswith("G00") or upper.startswith("G0 "):
            if current:
                segments.append(current)
                current = []
            continue
        if upper.startswith("G01") or upper.startswith("G1 ") or upper.startswith("G03") or upper.startswith("G3 "):
            current.append((x, y))
            continue
    if current:
        segments.append(current)
    return segments


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
        lead_in_length: float = 0.0,
        lead_out_length: float = 0.0,
        corner_radius: float = 0.0,
        name: str = "Toolpath",
        id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
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
        self.metadata = metadata or {}
        self.gcode: Optional[str] = None
        self.estimated_length: float = 0.0
        self.generated_at: Optional[str] = None

        # Basic feasibility
        radius = self.tool_diameter / 2.0
        if self.operation == "pocket" and (self.width <= self.tool_diameter or self.height <= self.tool_diameter):
            raise ToolpathValidationError("Tool too large for pocket")
        if self.strategy not in ("concentric", "zigzag", "spiral", "archimedean"):
            raise ToolpathValidationError(f"Unknown strategy: {self.strategy}")
        if self.operation not in ("pocket", "contour"):
            raise ToolpathValidationError(f"Unknown operation: {self.operation}")

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
        }
        if self.gcode is not None:
            data["gcode"] = self.gcode
        if self.estimated_length:
            data["estimated_length"] = self.estimated_length
        if self.generated_at:
            data["generated_at"] = self.generated_at
        if self.metadata:
            data["metadata"] = self.metadata
        return data

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
            feed=data.get("feed", 500.0),
            plunge_feed=data.get("plunge_feed", 150.0),
            safe_z=data.get("safe_z", 5.0),
            spindle_speed=data.get("spindle_speed", 12000),
            origin_x=data.get("origin_x", 0.0),
            origin_y=data.get("origin_y", 0.0),
            unit=data.get("unit", "mm"),
            lead_in_length=data.get("lead_in_length", 0.0),
            lead_out_length=data.get("lead_out_length", 0.0),
            corner_radius=data.get("corner_radius", 0.0),
            name=data.get("name", "Toolpath"),
            id=data.get("id"),
            metadata=data.get("metadata"),
        )
        if "gcode" in data:
            job.gcode = data["gcode"]
        if "estimated_length" in data:
            job.estimated_length = data["estimated_length"]
        if "generated_at" in data:
            job.generated_at = data["generated_at"]
        return job

    def validate(self) -> None:
        validate_toolpath_data(self.to_dict())

    def generate(self) -> str:
        """Generate G-code and populate self.gcode / estimated_length."""
        lines: List[str] = []
        lines.append("(PyModeler toolpath)")
        lines.append(f"(Operation: {self.operation} {self.strategy})")
        lines.append("G21 ; metric")
        lines.append("G90 ; absolute")
        lines.append(f"S{_fmt(self.spindle_speed)} M3")
        lines.append(f"G00 Z{_fmt(self.safe_z)}")

        radius = self.tool_diameter / 2.0
        ox, oy = self.origin_x, self.origin_y

        # Compute cut levels
        levels = max(1, math.ceil(self.depth / self.depth_of_cut))
        z_steps = [-(i + 1) * min(self.depth_of_cut, self.depth - i * self.depth_of_cut) for i in range(levels)]
        # Ensure last reaches full depth
        z_steps[-1] = -self.depth

        total_len = 0.0
        prev_x, prev_y = ox, oy

        def move_to(x: float, y: float, z: Optional[float] = None, feed: Optional[float] = None, rapid: bool = False) -> None:
            nonlocal prev_x, prev_y, total_len
            cmd = "G00" if rapid else "G01"
            parts = [cmd]
            if abs(x - prev_x) > 1e-6:
                parts.append(f"X{_fmt(x)}")
            if abs(y - prev_y) > 1e-6:
                parts.append(f"Y{_fmt(y)}")
            if z is not None:
                parts.append(f"Z{_fmt(z)}")
            if feed is not None and not rapid:
                parts.append(f"F{_fmt(feed)}")
            lines.append(" ".join(parts))
            dist = math.hypot(x - prev_x, y - prev_y)
            total_len += dist
            prev_x, prev_y = x, y

        def arc_to(x: float, y: float, r: float, clockwise: bool = False) -> None:
            nonlocal prev_x, prev_y, total_len
            cmd = "G02" if clockwise else "G03"
            lines.append(f"{cmd} X{_fmt(x)} Y{_fmt(y)} R{_fmt(r)} F{_fmt(self.feed)}")
            # Approximate arc length as chord for estimation
            dist = math.hypot(x - prev_x, y - prev_y)
            total_len += dist * 1.1  # rough
            prev_x, prev_y = x, y

        for zi, z in enumerate(z_steps):
            if self.operation == "contour":
                # Outside offset
                inset = -radius
                self._emit_rectangle(lines, move_to, arc_to, ox, oy, self.width, self.height, inset, z, is_first=(zi == 0))
            else:
                # Pocket
                if self.strategy == "concentric":
                    self._emit_concentric(lines, move_to, arc_to, ox, oy, self.width, self.height, radius, z, is_first=(zi == 0))
                elif self.strategy == "zigzag":
                    self._emit_zigzag(lines, move_to, ox, oy, self.width, self.height, radius, z, is_first=(zi == 0))
                elif self.strategy == "spiral":
                    self._emit_spiral(lines, move_to, arc_to, ox, oy, self.width, self.height, radius, z, is_first=(zi == 0))
                elif self.strategy == "archimedean":
                    self._emit_archimedean(lines, move_to, ox, oy, self.width, self.height, radius, z, is_first=(zi == 0))

            # Retract
            lines.append(f"G00 Z{_fmt(self.safe_z)}")

        lines.append("M5")
        lines.append("M30")
        self.gcode = "\n".join(lines) + "\n"
        self.estimated_length = total_len
        self.generated_at = datetime.now(timezone.utc).isoformat()
        return self.gcode

    def _emit_rectangle(self, lines, move_to, arc_to, ox, oy, w, h, inset, z, is_first):
        """Emit a single rectangular path (for contour or one concentric pass)."""
        r = self.corner_radius
        # Effective rectangle after inset
        x0 = ox + inset
        y0 = oy + inset
        x1 = ox + w - inset
        y1 = oy + h - inset
        if x1 <= x0 or y1 <= y0:
            return

        # Lead-in
        entry_x, entry_y = x0, y0
        if self.lead_in_length > 0 and is_first:
            lead_x = entry_x - self.lead_in_length
            lines.append(f"G00 X{_fmt(lead_x)} Y{_fmt(entry_y)}")
            lines.append(f"G00 Z{_fmt(self.safe_z)}")
            lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
            move_to(entry_x, entry_y, feed=self.feed)
        else:
            lines.append(f"G00 X{_fmt(entry_x)} Y{_fmt(entry_y)}")
            lines.append(f"G00 Z{_fmt(self.safe_z)}")
            lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")

        # Path with optional corner arcs
        if r <= 0:
            move_to(x1, y0, feed=self.feed)
            move_to(x1, y1, feed=self.feed)
            move_to(x0, y1, feed=self.feed)
            move_to(x0, y0, feed=self.feed)
        else:
            # Straight + arc at each corner (simple G03 R)
            # Bottom
            move_to(x1 - r, y0, feed=self.feed)
            arc_to(x1, y0 + r, r)
            # Right
            move_to(x1, y1 - r, feed=self.feed)
            arc_to(x1 - r, y1, r)
            # Top
            move_to(x0 + r, y1, feed=self.feed)
            arc_to(x0, y1 - r, r)
            # Left
            move_to(x0, y0 + r, feed=self.feed)
            arc_to(x0 + r, y0, r)

        # Lead-out
        if self.lead_out_length > 0:
            move_to(x0 + self.lead_out_length, y0, feed=self.feed)

    def _emit_concentric(self, lines, move_to, arc_to, ox, oy, w, h, radius, z, is_first):
        step = self.tool_diameter * self.stepover_fraction
        inset = radius
        while True:
            self._emit_rectangle(lines, move_to, arc_to, ox, oy, w, h, inset, z, is_first and inset == radius)
            next_inset = inset + step
            if next_inset * 2 >= min(w, h) - 1e-3:
                break
            inset = next_inset
            is_first = False  # only first level gets special lead

    def _emit_zigzag(self, lines, move_to, ox, oy, w, h, radius, z, is_first):
        step = self.tool_diameter * self.stepover_fraction
        y = oy + radius
        direction = 1
        first = True
        while y < oy + h - radius:
            if direction > 0:
                x_start, x_end = ox + radius, ox + w - radius
            else:
                x_start, x_end = ox + w - radius, ox + radius
            if first and is_first:
                lines.append(f"G00 X{_fmt(x_start)} Y{_fmt(y)}")
                lines.append(f"G00 Z{_fmt(self.safe_z)}")
                lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
                first = False
            else:
                move_to(x_start, y, rapid=True)
                lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
            move_to(x_end, y, feed=self.feed)
            y += step
            direction *= -1

    def _emit_spiral(self, lines, move_to, arc_to, ox, oy, w, h, radius, z, is_first):
        """Emit a continuous rectangular spiral inward (single plunge per Z level).

        Generates successive inset rectangles connected by a short feed move on the
        bottom side so the tool stays down and spirals continuously. Supports optional
        corner-radius arcs (G03) when corner_radius > 0. Falls back to concentric
        behavior if the pocket is too small for multiple passes.
        """
        step = self.tool_diameter * self.stepover_fraction
        inset = radius
        first_pass = True
        r = self.corner_radius
        while True:
            # Effective rectangle after inset
            x0 = ox + inset
            y0 = oy + inset
            x1 = ox + w - inset
            y1 = oy + h - inset
            if x1 <= x0 or y1 <= y0:
                break

            if first_pass:
                # Plunge at outer start
                if self.lead_in_length > 0 and is_first:
                    lead_x = x0 - self.lead_in_length
                    lines.append(f"G00 X{_fmt(lead_x)} Y{_fmt(y0)}")
                    lines.append(f"G00 Z{_fmt(self.safe_z)}")
                    lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
                    move_to(x0, y0, feed=self.feed)
                else:
                    lines.append(f"G00 X{_fmt(x0)} Y{_fmt(y0)}")
                    lines.append(f"G00 Z{_fmt(self.safe_z)}")
                    lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
                first_pass = False
            else:
                # Connect from previous end to new start with feed
                move_to(x0, y0, feed=self.feed)

            # Emit the four sides, with optional corner arcs
            if r <= 0 or (x1 - x0) <= 2 * r or (y1 - y0) <= 2 * r:
                # Sharp or too small for arcs
                move_to(x1, y0, feed=self.feed)
                move_to(x1, y1, feed=self.feed)
                move_to(x0, y1, feed=self.feed)
                move_to(x0, y0, feed=self.feed)
            else:
                # Bottom
                move_to(x1 - r, y0, feed=self.feed)
                arc_to(x1, y0 + r, r)
                # Right
                move_to(x1, y1 - r, feed=self.feed)
                arc_to(x1 - r, y1, r)
                # Top
                move_to(x0 + r, y1, feed=self.feed)
                arc_to(x0, y1 - r, r)
                # Left
                move_to(x0, y0 + r, feed=self.feed)
                arc_to(x0 + r, y0, r)

            next_inset = inset + step
            if next_inset * 2 >= min(w, h) - 1e-3:
                break
            inset = next_inset

        # Optional lead-out on the final (innermost) rectangle
        if self.lead_out_length > 0 and not first_pass:
            move_to(x0 + self.lead_out_length, y0, feed=self.feed)

    def _emit_archimedean(self, lines, move_to, ox, oy, w, h, radius, z, is_first):
        """Emit a continuous Archimedean (polar) spiral on the inscribed circle.

        Useful for roughly circular or square pockets. The path is a true polar
        spiral r = r_outer - b * θ, approximated by short G01 segments.
        One plunge per Z-level at the outer start; continuous feed to center.
        Stepover controls radial pitch (b = stepover / (2π)).
        Falls back to a simple center plunge + circular finish if the pocket is tiny.
        """
        # Inscribed circle parameters
        cx = ox + w / 2.0
        cy = oy + h / 2.0
        r_outer = min(w, h) / 2.0 - radius
        if r_outer <= radius:
            # Too small: just plunge center and stop
            lines.append(f"G00 X{_fmt(cx)} Y{_fmt(cy)}")
            lines.append(f"G00 Z{_fmt(self.safe_z)}")
            lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
            return

        step = self.tool_diameter * self.stepover_fraction
        b = step / (2.0 * math.pi)  # radial decrease per radian
        if b <= 0:
            b = 0.1

        # Start at outer, angle 0
        theta = 0.0
        r = r_outer
        # Angular resolution: ~5° or finer near center
        dtheta = math.radians(5.0)

        # Plunge at outer start
        sx = cx + r * math.cos(theta)
        sy = cy + r * math.sin(theta)
        if self.lead_in_length > 0 and is_first:
            # Simple radial lead-in
            lead_r = r + self.lead_in_length
            lx = cx + lead_r * math.cos(theta)
            ly = cy + lead_r * math.sin(theta)
            lines.append(f"G00 X{_fmt(lx)} Y{_fmt(ly)}")
            lines.append(f"G00 Z{_fmt(self.safe_z)}")
            lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")
            move_to(sx, sy, feed=self.feed)
        else:
            lines.append(f"G00 X{_fmt(sx)} Y{_fmt(sy)}")
            lines.append(f"G00 Z{_fmt(self.safe_z)}")
            lines.append(f"G01 Z{_fmt(z)} F{_fmt(self.plunge_feed)}")

        # Spiral inward
        max_theta = (r_outer / b) + 2 * math.pi  # safety
        while r > 0.5 * radius and theta < max_theta:
            theta += dtheta
            r = r_outer - b * theta
            if r <= 0:
                r = 0.0
            px = cx + r * math.cos(theta)
            py = cy + r * math.sin(theta)
            move_to(px, py, feed=self.feed)
            if r <= 0.5 * radius:
                break

        # Optional lead-out (radial outward a bit)
        if self.lead_out_length > 0:
            out_r = min(r + self.lead_out_length, r_outer)
            ox_out = cx + out_r * math.cos(theta)
            oy_out = cy + out_r * math.sin(theta)
            move_to(ox_out, oy_out, feed=self.feed)
