"""Configurations: independent inputs that drive Part parameters and feature suppressions.

Inspired by Onshape's configuration system (independent lists, numeric variables, checkboxes)
rather than a single combinatorial design table.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import jsonschema
from jsonschema import Draft202012Validator

if TYPE_CHECKING:
    from .part import Part

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_CONFIG_SCHEMA_PATH = _SCHEMA_DIR / "configuration.schema.json"

with open(_CONFIG_SCHEMA_PATH, encoding="utf-8") as f:
    CONFIGURATION_SCHEMA = json.load(f)

_CONFIG_VALIDATOR = Draft202012Validator(CONFIGURATION_SCHEMA)


class ConfigurationValidationError(ValueError):
    """Raised when configuration data fails schema validation."""


def validate_configuration_data(data: dict) -> None:
    """Validate a dict against the ConfigurationSet JSON Schema."""
    errors = sorted(_CONFIG_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise ConfigurationValidationError(
            "Configuration schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "cfg") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class ConfigurationSet:
    """Independent configuration inputs for a Part."""

    def __init__(
        self,
        name: str = "Configurations",
        inputs: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id()
        self.name = name
        self.inputs: List[dict] = inputs or []
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "inputs": self.inputs,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_configuration_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigurationSet":
        validate_configuration_data(data)
        return cls(
            name=data.get("name", "Configurations"),
            inputs=data.get("inputs", []),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    # --- Builders ---

    def add_list_input(
        self,
        name: str,
        options: List[dict],
    ) -> None:
        """Add a list input. Each option may contain parameter_overrides and suppressed_features."""
        inp = {
            "name": name,
            "type": "list",
            "options": options,
        }
        self.inputs.append(inp)
        self.validate()

    def add_numeric_input(
        self,
        name: str,
        target_parameter: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        default: Optional[float] = None,
    ) -> None:
        inp: dict[str, Any] = {
            "name": name,
            "type": "numeric",
            "target_parameter": target_parameter,
        }
        if min_val is not None:
            inp["min"] = float(min_val)
        if max_val is not None:
            inp["max"] = float(max_val)
        if default is not None:
            inp["default"] = float(default)
        self.inputs.append(inp)
        self.validate()

    def add_boolean_input(
        self,
        name: str,
        target_parameter: Optional[str] = None,
        target_feature: Optional[str] = None,
        true_value: Optional[float] = None,
        false_value: Optional[float] = None,
        suppress_when_false: bool = True,
    ) -> None:
        inp: dict[str, Any] = {
            "name": name,
            "type": "boolean",
            "suppress_when_false": suppress_when_false,
        }
        if target_parameter is not None:
            inp["target_parameter"] = target_parameter
        if target_feature is not None:
            inp["target_feature"] = target_feature
        if true_value is not None:
            inp["true_value"] = float(true_value)
        if false_value is not None:
            inp["false_value"] = float(false_value)
        self.inputs.append(inp)
        self.validate()

    def get_input(self, name: str) -> Optional[dict]:
        for inp in self.inputs:
            if inp["name"] == name:
                return inp
        return None

    # --- Application ---

    def apply(self, part: "Part", selections: Dict[str, Any]) -> None:
        """Apply the given input selections to a Part.

        selections: dict mapping input name → selected value
          - list: option name (str)
          - numeric: float
          - boolean: bool
        """
        # Clear previous suppressions that might have been set by configs
        # (we only clear ones that are currently marked; caller can recompute after)
        for fdict in part.feature_history.features:
            if fdict.get("_config_suppressed"):
                fdict.pop("suppressed", None)
                fdict.pop("_config_suppressed", None)

        for inp in self.inputs:
            name = inp["name"]
            if name not in selections:
                continue
            value = selections[name]
            itype = inp["type"]

            if itype == "list":
                option = next((o for o in inp["options"] if o["name"] == value), None)
                if option is None:
                    raise ConfigurationValidationError(
                        f"Unknown option '{value}' for list input '{name}'"
                    )
                overrides = option.get("parameter_overrides", {})
                for pname, pval in overrides.items():
                    if part.parameters.get(pname) is None:
                        part.parameters.add(pname, value=pval)
                    else:
                        part.parameters.update(pname, value=pval)
                for fid in option.get("suppressed_features", []):
                    self._suppress_feature(part, fid)

            elif itype == "numeric":
                target = inp["target_parameter"]
                try:
                    num = float(value)
                except (TypeError, ValueError) as e:
                    raise ConfigurationValidationError(
                        f"Numeric input '{name}' requires a number"
                    ) from e
                if "min" in inp and num < inp["min"]:
                    raise ConfigurationValidationError(
                        f"Value {num} below min {inp['min']} for '{name}'"
                    )
                if "max" in inp and num > inp["max"]:
                    raise ConfigurationValidationError(
                        f"Value {num} above max {inp['max']} for '{name}'"
                    )
                if part.parameters.get(target) is None:
                    part.parameters.add(target, value=num)
                else:
                    part.parameters.update(target, value=num)

            elif itype == "boolean":
                flag = bool(value)
                if "target_parameter" in inp:
                    target = inp["target_parameter"]
                    true_v = inp.get("true_value", 1.0)
                    false_v = inp.get("false_value", 0.0)
                    pval = true_v if flag else false_v
                    if part.parameters.get(target) is None:
                        part.parameters.add(target, value=pval)
                    else:
                        part.parameters.update(target, value=pval)
                if "target_feature" in inp and not flag and inp.get("suppress_when_false", True):
                    self._suppress_feature(part, inp["target_feature"])

        # Force recompute path to see updated parameters / suppressions
        part._body = None

    def _suppress_feature(self, part: "Part", feature_id: str) -> None:
        for fdict in part.feature_history.features:
            if fdict.get("id") == feature_id:
                fdict["suppressed"] = True
                fdict["_config_suppressed"] = True
                return
        # Silently ignore missing feature ids (or raise if preferred)
        # raise ConfigurationValidationError(f"Feature '{feature_id}' not found")
