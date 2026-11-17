"""Material and stock definitions for Parts and manufacturing helpers.

A Material describes physical/stock attributes (thickness, category, grain, etc.).
MaterialStore is a schema-validated library of materials that Parts can reference
by id or by embedding a material object.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        raise MaterialValidationError(
            "Material schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "mat") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _normalize_material(entry: dict) -> dict:
    """Ensure required defaults and id are present for a single material dict."""
    m = dict(entry)
    if "id" not in m or not m["id"]:
        m["id"] = _new_id()
    m.setdefault("category", "other")
    m.setdefault("type", "sheet")
    m.setdefault("grain", False)
    m.setdefault("unit", "mm")
    # Explicit nulls are allowed by schema; leave thickness/width/etc. as-is
    return m


class MaterialStore:
    """Schema-compliant library of material / stock definitions."""

    def __init__(
        self,
        name: str = "Materials",
        materials: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("matstore")
        self.name = name
        self.materials: List[dict] = [
            _normalize_material(m) for m in (materials or [])
        ]
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "materials": list(self.materials),
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

    def names(self) -> List[str]:
        return [m["name"] for m in self.materials]

    def get(self, name_or_id: str) -> Optional[dict]:
        """Return the first material matching name or id, or None."""
        for m in self.materials:
            if m.get("name") == name_or_id or m.get("id") == name_or_id:
                return m
        return None

    def add(
        self,
        name: str,
        *,
        category: str = "other",
        type: str = "sheet",
        thickness: Optional[float] = None,
        width: Optional[float] = None,
        length: Optional[float] = None,
        density: Optional[float] = None,
        color: Optional[str] = None,
        grain: bool = False,
        unit: str = "mm",
        cost_per_unit: Optional[float] = None,
        comment: Optional[str] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ) -> dict:
        """Add a material definition. Returns the created material dict."""
        if any(m["name"] == name for m in self.materials):
            raise MaterialValidationError(f"Material name already exists: {name}")
        entry: dict[str, Any] = {
            "id": id or _new_id(),
            "name": name,
            "category": category,
            "type": type,
            "grain": grain,
            "unit": unit,
        }
        if thickness is not None:
            entry["thickness"] = float(thickness)
        if width is not None:
            entry["width"] = float(width)
        if length is not None:
            entry["length"] = float(length)
        if density is not None:
            entry["density"] = float(density)
        if color is not None:
            entry["color"] = color
        if cost_per_unit is not None:
            entry["cost_per_unit"] = float(cost_per_unit)
        if comment is not None:
            entry["comment"] = comment
        if metadata:
            entry["metadata"] = metadata
        entry = _normalize_material(entry)
        self.materials.append(entry)
        self.validate()
        return entry

    def remove(self, name_or_id: str) -> bool:
        """Remove material by name or id. Returns True if removed."""
        for i, m in enumerate(self.materials):
            if m.get("name") == name_or_id or m.get("id") == name_or_id:
                del self.materials[i]
                self.validate()
                return True
        return False

    def update(self, name_or_id: str, **kwargs: Any) -> dict:
        """Update fields of an existing material. Returns the updated dict."""
        m = self.get(name_or_id)
        if m is None:
            raise MaterialValidationError(f"Material not found: {name_or_id}")
        # Protect identity keys if provided as None
        for key, value in kwargs.items():
            if key in ("id", "name") and value is None:
                continue
            if value is None and key in m:
                # Allow clearing optional numeric fields
                if key in ("thickness", "width", "length", "density", "color", "cost_per_unit", "comment"):
                    m.pop(key, None)
                continue
            m[key] = value
        self.validate()
        return m

    def __len__(self) -> int:
        return len(self.materials)

    def __repr__(self) -> str:
        return f"<MaterialStore id={self.id!r} name={self.name!r} count={len(self.materials)}>"


def create_default_library() -> MaterialStore:
    """Return a small starter library of common panel/stock materials."""
    store = MaterialStore(name="Default Materials")
    store.add(
        "Baltic Birch 18mm",
        category="wood",
        type="sheet",
        thickness=18.0,
        grain=True,
        color="#d4b896",
        density=680.0,
        comment="Common cabinet plywood",
    )
    store.add(
        "MDF 19mm",
        category="wood",
        type="sheet",
        thickness=19.0,
        grain=False,
        color="#b0a090",
        density=750.0,
    )
    store.add(
        "Aluminum 6061",
        category="metal",
        type="solid",
        density=2700.0,
        color="#c0c0c0",
        comment="General-purpose aluminum alloy",
    )
    store.add(
        "Acrylic 6mm",
        category="plastic",
        type="sheet",
        thickness=6.0,
        grain=False,
        color="#e8f4f8",
        density=1190.0,
    )
    return store
