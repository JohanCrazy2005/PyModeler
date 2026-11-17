"""Basic Bill of Materials (BOM) generation.

Aggregates unique Parts (from a list or from an Assembly) with summed quantities,
resolved materials, and optional bounding-box size of the recomputed body.

Validated against schemas/bom.schema.json.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
from jsonschema import Draft202012Validator

from .assembly import Assembly
from .cutlist import _bounding_box_size, _resolve_material
from .material import MaterialStore
from .part import Part

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_BOM_SCHEMA_PATH = _SCHEMA_DIR / "bom.schema.json"

with open(_BOM_SCHEMA_PATH, encoding="utf-8") as f:
    BOM_SCHEMA = json.load(f)

_BOM_VALIDATOR = Draft202012Validator(BOM_SCHEMA)


class BOMValidationError(ValueError):
    """Raised when BOM data fails schema validation."""


def validate_bom_data(data: dict) -> None:
    """Validate a dict against the BOM JSON Schema."""
    errors = sorted(_BOM_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise BOMValidationError(
            "BOM schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "bom") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def generate_bom(
    parts: Optional[Union[Part, Sequence[Part]]] = None,
    assembly: Optional[Assembly] = None,
    parts_map: Optional[Dict[str, Part]] = None,
    material_store: Optional[MaterialStore] = None,
    quantities: Optional[Dict[str, int]] = None,
    name: str = "BOM",
    id: Optional[str] = None,
) -> dict:
    """Generate a schema-validated BOM from Parts or an Assembly.

    Parameters
    ----------
    parts : Part or sequence of Parts (used when no assembly is given)
    assembly : optional Assembly whose instances are counted by part_id
    parts_map : optional dict part_id → Part used to resolve Assembly instances
    material_store : optional MaterialStore for name/id resolution
    quantities : optional map of part_id → quantity (defaults to 1; for assembly this is added to instance counts)
    name, id : metadata for the resulting document

    Returns
    -------
    dict
        Valid BOM document. Items are unique by part_id with summed quantities.
    """
    parts_map = parts_map or {}
    quantities = quantities or {}
    source = "parts"
    counted: Dict[str, int] = defaultdict(int)
    resolved_parts: Dict[str, Part] = {}

    if assembly is not None:
        source = "assembly"
        for inst in assembly.instances:
            pid = inst.part_id
            counted[pid] += 1
            # Prefer runtime reference, then parts_map
            if inst.part is not None:
                resolved_parts[pid] = inst.part
            elif pid in parts_map:
                resolved_parts[pid] = parts_map[pid]
        # Apply extra quantities on top of instance counts
        for pid, extra in quantities.items():
            counted[pid] += int(extra)
            if pid in parts_map and pid not in resolved_parts:
                resolved_parts[pid] = parts_map[pid]
    else:
        if parts is None:
            parts = []
        if isinstance(parts, Part):
            parts = [parts]
        parts = list(parts)
        for part in parts:
            counted[part.id] += int(quantities.get(part.id, 1))
            resolved_parts[part.id] = part

    items: List[dict] = []
    for pid, qty in sorted(counted.items()):
        part = resolved_parts.get(pid)
        if part is None:
            # Unresolved part_id (possible when only assembly ids are known)
            item: dict[str, Any] = {
                "part_id": pid,
                "name": pid,
                "quantity": int(qty),
                "has_geometry": False,
            }
            items.append(item)
            continue

        body = part.recompute()
        bb = _bounding_box_size(body)
        mat_name, mat_id, raw_mat = _resolve_material(part.material, material_store)

        item = {
            "part_id": part.id,
            "name": part.name,
            "quantity": int(qty),
            "material": raw_mat,
            "material_name": mat_name,
            "material_id": mat_id,
            "has_geometry": body is not None,
        }
        if bb is not None:
            item["size"] = {
                "width": bb["width"],
                "depth": bb["depth"],
                "height": bb["height"],
                "dx": bb["dx"],
                "dy": bb["dy"],
                "dz": bb["dz"],
                "unit": bb["unit"],
            }
        items.append(item)

    data: dict[str, Any] = {
        "id": id or _new_id(),
        "name": name,
        "source": source,
        "items": items,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    validate_bom_data(data)
    return data


def bom_to_csv(bom: dict) -> str:
    """Export a BOM to CSV string.

    Columns: quantity, name, material_name, width, depth, height, part_id
    """
    validate_bom_data(bom)
    output = io.StringIO()
    fieldnames = [
        "quantity",
        "name",
        "material_name",
        "width",
        "depth",
        "height",
        "part_id",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for item in bom.get("items", []):
        size = item.get("size") or {}
        row = {
            "quantity": item.get("quantity", 1),
            "name": item.get("name", ""),
            "material_name": item.get("material_name") or "",
            "width": size.get("width", ""),
            "depth": size.get("depth", ""),
            "height": size.get("height", ""),
            "part_id": item.get("part_id", ""),
        }
        writer.writerow(row)
    return output.getvalue()


def bom_to_text(bom: dict) -> str:
    """Pretty-print a BOM as a simple text table."""
    lines = [
        f"BOM: {bom.get('name', 'BOM')} (source: {bom.get('source', 'parts')})",
        f"Generated: {bom.get('generated_at', '')}",
        "-" * 72,
        f"{'Qty':>4}  {'Name':<20}  {'Material':<22}  {'Size (W x D x H)':<24}",
        "-" * 72,
    ]
    for it in bom.get("items", []):
        qty = it.get("quantity", 1)
        name = (it.get("name") or "")[:20]
        mat = (it.get("material_name") or "-")[:22]
        sz = it.get("size") or {}
        if sz and sz.get("width") is not None:
            size_str = f"{sz.get('width', 0):.1f} x {sz.get('depth', 0):.1f} x {sz.get('height', 0):.1f}"
        else:
            size_str = "(no geometry)"
        lines.append(f"{qty:>4}  {name:<20}  {mat:<22}  {size_str:<24}")
    lines.append("-" * 72)
    lines.append(f"Total unique parts: {len(bom.get('items', []))}")
    total_qty = sum(it.get("quantity", 1) for it in bom.get("items", []))
    lines.append(f"Total quantity: {total_qty}")
    return "\n".join(lines)


class BOM:
    """Thin wrapper around a validated BOM document."""

    def __init__(self, data: dict):
        validate_bom_data(data)
        self.data = data

    @classmethod
    def from_parts(
        cls,
        parts: Union[Part, Sequence[Part]],
        material_store: Optional[MaterialStore] = None,
        quantities: Optional[Dict[str, int]] = None,
        name: str = "BOM",
    ) -> "BOM":
        data = generate_bom(parts=parts, material_store=material_store, quantities=quantities, name=name)
        return cls(data)

    @classmethod
    def from_assembly(
        cls,
        assembly: Assembly,
        parts_map: Optional[Dict[str, Part]] = None,
        material_store: Optional[MaterialStore] = None,
        quantities: Optional[Dict[str, int]] = None,
        name: str = "BOM",
    ) -> "BOM":
        data = generate_bom(
            assembly=assembly,
            parts_map=parts_map,
            material_store=material_store,
            quantities=quantities,
            name=name,
        )
        return cls(data)

    def to_dict(self) -> dict:
        return dict(self.data)

    def to_text(self) -> str:
        return bom_to_text(self.data)

    def to_csv(self) -> str:
        return bom_to_csv(self.data)

    def __repr__(self) -> str:
        return f"<BOM name={self.data.get('name')!r} items={len(self.data.get('items', []))}>"
