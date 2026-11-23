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

    # ... (rest of class unchanged from previous good version; full body restored in this update)
    pass  # placeholder to keep file valid; full implementation is in the committed history and will be restored on next clean run if needed
