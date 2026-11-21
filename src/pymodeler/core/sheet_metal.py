"""Sheet-metal rules and basic bend calculations.

SheetMetalRuleStore holds schema-validated rules (thickness, inside bend radius,
K-factor, relief). bend_allowance implements the standard neutral-axis formula
used by Fusion, Onshape, and most CAD systems.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_RULE_SCHEMA_PATH = _SCHEMA_DIR / "sheet_metal_rule.schema.json"

with open(_RULE_SCHEMA_PATH, encoding="utf-8") as f:
    SHEET_METAL_RULE_SCHEMA = json.load(f)

_RULE_VALIDATOR = Draft202012Validator(SHEET_METAL_RULE_SCHEMA)


class SheetMetalRuleValidationError(ValueError):
    """Raised when sheet-metal rule data fails schema validation."""


def validate_sheet_metal_rule_data(data: dict) -> None:
    """Validate a dict against the SheetMetalRuleStore JSON Schema."""
    errors = sorted(_RULE_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise SheetMetalRuleValidationError(
            "Sheet metal rule schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "smr") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _normalize_rule(entry: dict) -> dict:
    """Ensure required defaults and id are present for a single rule dict."""
    r = dict(entry)
    if "id" not in r or not r["id"]:
        r["id"] = _new_id()
    r.setdefault("relief_type", "rectangular")
    r.setdefault("unit", "mm")
    return r


class SheetMetalRuleStore:
    """Schema-compliant library of sheet-metal rules."""

    def __init__(
        self,
        name: str = "Sheet Metal Rules",
        rules: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("smstore")
        self.name = name
        self.rules: List[dict] = [_normalize_rule(r) for r in (rules or [])]
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "rules": list(self.rules),
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_sheet_metal_rule_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "SheetMetalRuleStore":
        validate_sheet_metal_rule_data(data)
        return cls(
            name=data.get("name", "Sheet Metal Rules"),
            rules=data.get("rules", []),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def names(self) -> List[str]:
        return [r["name"] for r in self.rules]

    def get(self, name_or_id: str) -> Optional[dict]:
        """Return the first rule matching name or id, or None."""
        for r in self.rules:
            if r.get("name") == name_or_id or r.get("id") == name_or_id:
                return r
        return None

    def add(
        self,
        name: str,
        *,
        thickness: float,
        bend_radius: float,
        k_factor: float,
        relief_type: str = "rectangular",
        unit: str = "mm",
        comment: Optional[str] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ) -> dict:
        """Add a sheet-metal rule. Returns the created rule dict."""
        if any(r["name"] == name for r in self.rules):
            raise SheetMetalRuleValidationError(f"Rule name already exists: {name}")
        entry: dict[str, Any] = {
            "id": id or _new_id(),
            "name": name,
            "thickness": float(thickness),
            "bend_radius": float(bend_radius),
            "k_factor": float(k_factor),
            "relief_type": relief_type,
            "unit": unit,
        }
        if comment is not None:
            entry["comment"] = comment
        if metadata:
            entry["metadata"] = metadata
        entry = _normalize_rule(entry)
        self.rules.append(entry)
        self.validate()
        return entry

    def remove(self, name_or_id: str) -> bool:
        """Remove rule by name or id. Returns True if removed."""
        for i, r in enumerate(self.rules):
            if r.get("name") == name_or_id or r.get("id") == name_or_id:
                del self.rules[i]
                self.validate()
                return True
        return False

    def __len__(self) -> int:
        return len(self.rules)

    def __repr__(self) -> str:
        return f"<SheetMetalRuleStore id={self.id!r} name={self.name!r} count={len(self.rules)}>"


def bend_allowance(
    thickness: float,
    bend_radius: float,
    k_factor: float,
    angle_deg: float,
) -> float:
    """Compute bend allowance along the neutral axis.

    BA = (π / 180) * angle_deg * (R + K * T)

    Args:
        thickness: Sheet thickness T.
        bend_radius: Inside bend radius R.
        k_factor: Neutral-axis factor K (0 ≤ K ≤ 0.5).
        angle_deg: Bend angle in degrees (positive).

    Returns:
        Bend allowance length in the same units as thickness / radius.
    """
    if thickness <= 0:
        raise ValueError("thickness must be positive")
    if bend_radius < 0:
        raise ValueError("bend_radius must be non-negative")
    if not (0 <= k_factor <= 0.5):
        raise ValueError("k_factor must be in [0, 0.5]")
    if angle_deg < 0:
        raise ValueError("angle_deg must be non-negative")
    return (math.pi / 180.0) * angle_deg * (bend_radius + k_factor * thickness)


def create_default_sheet_metal_rules() -> SheetMetalRuleStore:
    """Return a small starter library of common sheet-metal rules."""
    store = SheetMetalRuleStore(name="Default Sheet Metal Rules")
    store.add(
        "Mild Steel 1.5mm",
        thickness=1.5,
        bend_radius=1.5,
        k_factor=0.40,
        relief_type="rectangular",
        comment="Typical air-bend mild steel, R/T ≈ 1",
    )
    store.add(
        "Mild Steel 2.0mm",
        thickness=2.0,
        bend_radius=2.0,
        k_factor=0.42,
        relief_type="rectangular",
    )
    store.add(
        "Aluminum 2.0mm",
        thickness=2.0,
        bend_radius=2.0,
        k_factor=0.38,
        relief_type="round",
        comment="Softer alloy, slightly lower K",
    )
    store.add(
        "Stainless 1.0mm",
        thickness=1.0,
        bend_radius=1.5,
        k_factor=0.44,
        relief_type="tear",
    )
    return store
