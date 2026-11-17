"""Material / stock definitions for manufacturing-aware parametric parts.

Simple schema-driven store so Parts can reference named materials (thickness, type, cost, etc.).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_MATERIAL_SCHEMA_PATH = _SCHEMA_DIR / "material.schema.json"

with open(_MATERIAL_SCHEMA_PATH, encoding="utf-8") as f:
    MATERIAL_SCHEMA = json.load(f)

_MATERIAL_VALIDATOR = Draft202012Validator(MATERIAL_SCHEMA)


class MaterialValidationError(ValueError):
    """Raised when material data fails schema validation."""


def validate_material_data(data: dict) -> None:
    """Validate a dict against the MaterialStore JSON Schema."""
    errors = sorted(_MATERIAL_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise MaterialValidationError("Material schema validation failed:\n" + "\n".join(messages))


class MaterialStore:
    """Schema-compliant store of named materials / stock."""

    def __init__(
        self,
        name: str = "Materials",
        materials: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or f"mats_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.materials: List[dict] = materials or []
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "materials": self.materials,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_material_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "MaterialStore":
        validate_material_data(data)
        return cls(
            name=data.get("name", "Materials"),
            materials=data.get("materials", []),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add(
        self,
        name: str,
        thickness: Optional[float] = None,
        type: Optional[str] = None,
        unit: str = "mm",
        density: Optional[float] = None,
        cost: Optional[float] = None,
        grain_direction: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Add a material definition. Returns the created dict."""
        mat: dict[str, Any] = {"name": name, "unit": unit}
        if thickness is not None:
            mat["thickness"] = float(thickness)
        if type is not None:
            mat["type"] = type
        if density is not None:
            mat["density"] = float(density)
        if cost is not None:
            mat["cost"] = float(cost)
        if grain_direction is not None:
            mat["grain_direction"] = grain_direction
        if comment is not None:
            mat["comment"] = comment
        if metadata is not None:
            mat["metadata"] = metadata
        # Replace if name exists
        self.materials = [m for m in self.materials if m.get("name") != name]
        self.materials.append(mat)
        self.validate()
        return mat

    def get(self, name: str) -> Optional[dict]:
        for m in self.materials:
            if m.get("name") == name:
                return m
        return None

    def names(self) -> List[str]:
        return [m["name"] for m in self.materials]

    def __repr__(self) -> str:
        return f"<MaterialStore id={self.id!r} name={self.name!r} count={len(self.materials)}>"
