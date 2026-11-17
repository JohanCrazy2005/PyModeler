"""Simple Assembly: container for Part instances with transforms.

Validated against schemas/assembly.schema.json.
Mates and constraint solving are intentionally deferred.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from jsonschema import Draft202012Validator

from .part import Part
from .scene import Transform

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_ASSEMBLY_SCHEMA_PATH = _SCHEMA_DIR / "assembly.schema.json"

with open(_ASSEMBLY_SCHEMA_PATH, encoding="utf-8") as f:
    ASSEMBLY_SCHEMA = json.load(f)

_ASSEMBLY_VALIDATOR = Draft202012Validator(ASSEMBLY_SCHEMA)


class AssemblyValidationError(ValueError):
    """Raised when Assembly data fails schema validation."""


def validate_assembly_data(data: dict) -> None:
    errors = sorted(_ASSEMBLY_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise AssemblyValidationError(
            "Assembly schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "asm") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Instance:
    """One placement of a Part inside an Assembly."""

    def __init__(
        self,
        part_id: str,
        transform: Optional[Transform] = None,
        name: Optional[str] = None,
        grounded: bool = False,
        visible: bool = True,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
        part: Optional[Part] = None,
    ):
        self.id = id or _new_id("inst")
        self.part_id = part_id
        self.name = name or part_id
        self.transform = transform or Transform()
        self.grounded = grounded
        self.visible = visible
        self.metadata = metadata or {}
        self.part = part  # runtime reference; not serialized directly

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "part_id": self.part_id,
            "transform": self.transform.to_dict(),
            "grounded": self.grounded,
            "visible": self.visible,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    @classmethod
    def from_dict(cls, data: dict, part: Optional[Part] = None) -> "Instance":
        return cls(
            part_id=data["part_id"],
            transform=Transform.from_dict(data.get("transform")),
            name=data.get("name"),
            grounded=data.get("grounded", False),
            visible=data.get("visible", True),
            metadata=data.get("metadata"),
            id=data.get("id"),
            part=part,
        )


class Assembly:
    """Collection of Part instances with placement transforms."""

    def __init__(
        self,
        name: str = "Assembly",
        instances: Optional[List[Instance]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("asm")
        self.name = name
        self.instances: List[Instance] = instances or []
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "instances": [inst.to_dict() for inst in self.instances],
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_assembly_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict, parts: Optional[Dict[str, Part]] = None) -> "Assembly":
        validate_assembly_data(data)
        parts = parts or {}
        instances = []
        for idata in data.get("instances", []):
            part = parts.get(idata.get("part_id"))
            instances.append(Instance.from_dict(idata, part=part))
        return cls(
            name=data.get("name", "Assembly"),
            instances=instances,
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def add_instance(
        self,
        part: Part,
        transform: Optional[Transform] = None,
        name: Optional[str] = None,
        grounded: bool = False,
        visible: bool = True,
    ) -> Instance:
        """Add a Part instance. Stores the runtime Part reference."""
        inst = Instance(
            part_id=part.id,
            transform=transform or Transform(),
            name=name or part.name,
            grounded=grounded,
            visible=visible,
            part=part,
        )
        self.instances.append(inst)
        self.validate()
        return inst

    def remove_instance(self, instance_id: str) -> bool:
        before = len(self.instances)
        self.instances = [i for i in self.instances if i.id != instance_id]
        if len(self.instances) < before:
            self.validate()
            return True
        return False

    def get_instance(self, instance_id: str) -> Optional[Instance]:
        for inst in self.instances:
            if inst.id == instance_id:
                return inst
        return None

    def __repr__(self) -> str:
        return f"<Assembly id={self.id!r} name={self.name!r} instances={len(self.instances)}>"
