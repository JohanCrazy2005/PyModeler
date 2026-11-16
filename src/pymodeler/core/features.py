"""Parametric features (Extrude, Revolve, etc.) and feature history.

ExtrudeFeature turns a Sketch into a solid mesh driven by a numeric distance
or a ParameterStore reference. RevolveFeature rotates a profile around an axis.
FeatureHistory is a serializable timeline.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import jsonschema
from jsonschema import Draft202012Validator

from .mesh import Mesh
from .parameters import ParameterStore
from .sketch import Sketch

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_EXTRUDE_SCHEMA_PATH = _SCHEMA_DIR / "extrude.schema.json"
_REVOLVE_SCHEMA_PATH = _SCHEMA_DIR / "revolve.schema.json"
_HISTORY_SCHEMA_PATH = _SCHEMA_DIR / "feature_history.schema.json"

with open(_EXTRUDE_SCHEMA_PATH, encoding="utf-8") as f:
    EXTRUDE_SCHEMA = json.load(f)
with open(_REVOLVE_SCHEMA_PATH, encoding="utf-8") as f:
    REVOLVE_SCHEMA = json.load(f)
with open(_HISTORY_SCHEMA_PATH, encoding="utf-8") as f:
    HISTORY_SCHEMA = json.load(f)

_EXTRUDE_VALIDATOR = Draft202012Validator(EXTRUDE_SCHEMA)
_REVOLVE_VALIDATOR = Draft202012Validator(REVOLVE_SCHEMA)
_HISTORY_VALIDATOR = Draft202012Validator(HISTORY_SCHEMA)


class FeatureValidationError(ValueError):
    """Raised when feature or history data fails schema validation."""


def validate_extrude_data(data: dict) -> None:
    errors = sorted(_EXTRUDE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Extrude schema validation failed:\n" + "\n".join(messages))


def validate_revolve_data(data: dict) -> None:
    errors = sorted(_REVOLVE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("Revolve schema validation failed:\n" + "\n".join(messages))


def validate_history_data(data: dict) -> None:
    errors = sorted(_HISTORY_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise FeatureValidationError("FeatureHistory schema validation failed:\n" + "\n".join(messages))


def _new_id(prefix: str = "feat") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _resolve_distance(distance: float | str, parameters: Optional[ParameterStore] = None) -> float:
    """Resolve a distance that may be numeric or a parameter name / simple expression."""
    if isinstance(distance, (int, float)):
        return float(distance)
    if not isinstance(distance, str) or not distance.strip():
        raise FeatureValidationError("Distance must be a number or non-empty string")
    # Try as bare parameter name first
    if parameters is not None and parameters.get(distance) is not None:
        return parameters.evaluate(distance)
    # Fall back to evaluating as an expression if it looks like one
    if parameters is not None:
        try:
            # Re-use ParameterStore evaluation by temporary param
            tmp_name = "__tmp_dist__"
            if parameters.get(tmp_name) is None:
                parameters.add(tmp_name, expression=distance)
            try:
                return parameters.evaluate(tmp_name)
            finally:
                parameters.remove(tmp_name)
        except Exception:
            pass
    # Last resort: try float conversion
    try:
        return float(distance)
    except ValueError as e:
        raise FeatureValidationError(f"Cannot resolve distance '{distance}'") from e
