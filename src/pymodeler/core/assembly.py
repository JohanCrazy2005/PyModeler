"""Simple Assembly: container for Part instances with transforms and basic mates.

Validated against schemas/assembly.schema.json.
Supports rigid / fastened mates with location + rotation offset solver.
Revolute / slider types accepted as stubs (currently apply fixed offset).
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


class Mate:
    """A mate locking or constraining the relative transform of two instances.

    Types: rigid/fastened (0 DOF), revolute/slider (stubs).
    """

    def __init__(
        self,
        instance_a: str,
        instance_b: str,
        type: str = "rigid",
        offset: Optional[Transform] = None,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        if type not in ("rigid", "fastened", "revolute", "slider"):
            raise ValueError(f"Unsupported mate type: {type}")
        self.id = id or _new_id("mate")
        self.name = name or f"{type.capitalize()} Mate"
        self.type = type
        self.instance_a = instance_a
        self.instance_b = instance_b
        self.offset = offset or Transform()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "instance_a": self.instance_a,
            "instance_b": self.instance_b,
        }
        offset_dict = self.offset.to_dict()
        if offset_dict != {"location": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]}:
            data["offset"] = offset_dict
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Mate":
        return cls(
            instance_a=data["instance_a"],
            instance_b=data["instance_b"],
            type=data.get("type", "rigid"),
            offset=Transform.from_dict(data.get("offset")),
            name=data.get("name"),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )


class Assembly:
    """Collection of Part instances with placement transforms."""

    def __init__(
        self,
        name: str = "Assembly",
        instances: Optional[List[Instance]] = None,
        mates: Optional[List[Mate]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or _new_id("asm")
        self.name = name
        self.instances: List[Instance] = instances or []
        self.mates: List[Mate] = mates or []
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "instances": [inst.to_dict() for inst in self.instances],
        }
        if self.mates:
            data["mates"] = [m.to_dict() for m in self.mates]
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
        mates = [Mate.from_dict(m) for m in data.get("mates", [])]
        return cls(
            name=data.get("name", "Assembly"),
            instances=instances,
            mates=mates,
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

    def add_mate(
        self,
        instance_a: Instance | str,
        instance_b: Instance | str,
        type: str = "rigid",
        offset: Optional[Transform] = None,
        name: Optional[str] = None,
    ) -> Mate:
        """Add a rigid/fastened mate between two instances."""
        id_a = instance_a.id if isinstance(instance_a, Instance) else instance_a
        id_b = instance_b.id if isinstance(instance_b, Instance) else instance_b
        if self.get_instance(id_a) is None or self.get_instance(id_b) is None:
            raise ValueError("Both instances must exist in the assembly")
        mate = Mate(instance_a=id_a, instance_b=id_b, type=type, offset=offset, name=name)
        self.mates.append(mate)
        self.validate()
        return mate

    def remove_mate(self, mate_id: str) -> bool:
        before = len(self.mates)
        self.mates = [m for m in self.mates if m.id != mate_id]
        if len(self.mates) < before:
            self.validate()
            return True
        return False

    def solve_mates(self) -> None:
        """Solver for mates.

        Rigid/fastened: set free instance location and rotation to grounded + offset
        (component-wise Euler addition as basic composition; full matrix composition later).
        Revolute/slider: currently apply the same fixed offset (stubs; DOF freeing later).
        Multiple mates applied in list order; last write wins for conflicts.
        If neither or both grounded, leave transforms as-is.
        """
        by_id = {inst.id: inst for inst in self.instances}
        for mate in self.mates:
            if mate.type not in ("rigid", "fastened", "revolute", "slider"):
                continue
            a = by_id.get(mate.instance_a)
            b = by_id.get(mate.instance_b)
            if a is None or b is None:
                continue
            ox, oy, oz = mate.offset.location
            orx, ory, orz = mate.offset.rotation
            if a.grounded and not b.grounded:
                b.transform.location = [
                    a.transform.location[0] + ox,
                    a.transform.location[1] + oy,
                    a.transform.location[2] + oz,
                ]
                b.transform.rotation = [
                    a.transform.rotation[0] + orx,
                    a.transform.rotation[1] + ory,
                    a.transform.rotation[2] + orz,
                ]
            elif b.grounded and not a.grounded:
                # Inverse: A should be B - offset
                a.transform.location = [
                    b.transform.location[0] - ox,
                    b.transform.location[1] - oy,
                    b.transform.location[2] - oz,
                ]
                a.transform.rotation = [
                    b.transform.rotation[0] - orx,
                    b.transform.rotation[1] - ory,
                    b.transform.rotation[2] - orz,
                ]
            # If neither or both grounded, leave transforms as-is (user responsibility)

    def __repr__(self) -> str:
        return f"<Assembly id={self.id!r} name={self.name!r} instances={len(self.instances)} mates={len(self.mates)}>"
