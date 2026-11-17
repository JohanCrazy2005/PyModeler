"""Cut list / part list generation (Mozaik-inspired stub).

Walks one or more Parts, recomputes their bodies, extracts axis-aligned
bounding-box size, and resolves material names via an optional MaterialStore.

Validated against schemas/cutlist.schema.json.
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

from .material import MaterialStore
from .part import Part

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_CUTLIST_SCHEMA_PATH = _SCHEMA_DIR / "cutlist.schema.json"

with open(_CUTLIST_SCHEMA_PATH, encoding="utf-8") as f:
    CUTLIST_SCHEMA = json.load(f)

_CUTLIST_VALIDATOR = Draft202012Validator(CUTLIST_SCHEMA)


class CutListValidationError(ValueError):
    """Raised when cut-list data fails schema validation."""


def validate_cutlist_data(data: dict) -> None:
    """Validate a dict against the CutList JSON Schema."""
    errors = sorted(_CUTLIST_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise CutListValidationError(
            "CutList schema validation failed:\n" + "\n".join(messages)
        )


def _new_id(prefix: str = "cutlist") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _resolve_material(
    material: Any,
    store: Optional[MaterialStore],
) -> tuple[Optional[str], Optional[str], Any]:
    """Return (material_name, material_id, raw_material)."""
    raw = material
    if material is None:
        return None, None, None
    if isinstance(material, str):
        if store is not None:
            found = store.get(material)
            if found:
                return found.get("name"), found.get("id"), raw
        return material, None, raw
    if isinstance(material, dict):
        name = material.get("name")
        mid = material.get("id")
        if store is not None and (name or mid):
            found = store.get(name or mid or "")
            if found:
                return found.get("name") or name, found.get("id") or mid, raw
        return name, mid, raw
    return str(material), None, raw


def _bounding_box_size(mesh) -> Optional[dict]:
    """Return size + min/max dict from mesh vertices, or None if empty."""
    if mesh is None or not mesh.vertices:
        return None
    verts = np.asarray(mesh.vertices, dtype=float)
    if verts.size == 0:
        return None
    mins = verts.min(axis=0).tolist()
    maxs = verts.max(axis=0).tolist()
    size = [maxs[i] - mins[i] for i in range(3)]
    # Report as width/depth/height using absolute extents (order preserved as X/Y/Z)
    return {
        "dx": float(size[0]),
        "dy": float(size[1]),
        "dz": float(size[2]),
        "width": float(size[0]),
        "depth": float(size[1]),
        "height": float(size[2]),
        "unit": "mm",
        "min": mins,
        "max": maxs,
    }


def generate_cut_list(
    parts: Union[Part, Sequence[Part]],
    material_store: Optional[MaterialStore] = None,
    quantities: Optional[Dict[str, int]] = None,
    name: str = "Cut List",
    id: Optional[str] = None,
) -> dict:
    """Generate a schema-validated cut list from one or more Parts.

    Parameters
    ----------
    parts : Part or sequence of Parts
    material_store : optional MaterialStore used to resolve string material ids/names
    quantities : optional map of part_id → quantity (defaults to 1)
    name, id : metadata for the resulting document

    Returns
    -------
    dict
        Valid CutList document. Each item contains quantity, resolved material_name,
        and bounding-box size of the recomputed body (or has_geometry=False).
    """
    if isinstance(parts, Part):
        parts = [parts]
    parts = list(parts)
    quantities = quantities or {}

    items: List[dict] = []
    for part in parts:
        # Ensure body is up to date
        body = part.recompute()
        bb = _bounding_box_size(body)
        mat_name, mat_id, raw_mat = _resolve_material(part.material, material_store)

        item: dict[str, Any] = {
            "part_id": part.id,
            "name": part.name,
            "quantity": int(quantities.get(part.id, 1)),
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
            item["bounding_box"] = {"min": bb["min"], "max": bb["max"]}
        items.append(item)

    data: dict[str, Any] = {
        "id": id or _new_id(),
        "name": name,
        "items": items,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    validate_cutlist_data(data)
    return data


def _item_thickness(item: dict) -> Optional[float]:
    """Best-effort thickness: prefer explicit material thickness, else min size dimension."""
    material = item.get("material")
    if isinstance(material, dict) and material.get("thickness") is not None:
        try:
            return float(material["thickness"])
        except (TypeError, ValueError):
            pass
    size = item.get("size") or {}
    dims = [size.get("width"), size.get("depth"), size.get("height")]
    dims = [float(d) for d in dims if d is not None]
    if dims:
        return min(dims)
    return None


def group_cut_list(cutlist: dict, by: str = "material_thickness") -> dict:
    """Group cut-list items by material and/or thickness.

    Parameters
    ----------
    cutlist : dict
        A validated cut-list document.
    by : str
        "material" | "thickness" | "material_thickness" (default).

    Returns
    -------
    dict
        Mapping of group key → list of items belonging to that group.
        Keys are human-readable strings (e.g. "Baltic Birch 18mm / 18.0 mm").
    """
    validate_cutlist_data(cutlist)
    groups: Dict[str, List[dict]] = defaultdict(list)
    for item in cutlist.get("items", []):
        mat = item.get("material_name") or "(no material)"
        thick = _item_thickness(item)
        thick_str = f"{thick:.1f} mm" if thick is not None else "(no thickness)"
        if by == "material":
            key = mat
        elif by == "thickness":
            key = thick_str
        else:  # material_thickness
            key = f"{mat} / {thick_str}"
        groups[key].append(item)
    return dict(groups)


def cut_list_to_csv(cutlist: dict, include_groups: bool = False) -> str:
    """Export a cut list to CSV string (Mozaik-style helper).

    Columns: quantity, name, material_name, width, depth, height, thickness, part_id
    When include_groups=True a group column is added (material + thickness).
    """
    validate_cutlist_data(cutlist)
    output = io.StringIO()
    fieldnames = [
        "quantity",
        "name",
        "material_name",
        "width",
        "depth",
        "height",
        "thickness",
        "part_id",
    ]
    if include_groups:
        fieldnames.insert(0, "group")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    groups = group_cut_list(cutlist) if include_groups else {}
    # reverse lookup item → group
    item_to_group = {}
    if include_groups:
        for gkey, gitems in groups.items():
            for it in gitems:
                item_to_group[id(it)] = gkey
    for item in cutlist.get("items", []):
        size = item.get("size") or {}
        row = {
            "quantity": item.get("quantity", 1),
            "name": item.get("name", ""),
            "material_name": item.get("material_name") or "",
            "width": size.get("width", ""),
            "depth": size.get("depth", ""),
            "height": size.get("height", ""),
            "thickness": _item_thickness(item) or "",
            "part_id": item.get("part_id", ""),
        }
        if include_groups:
            row["group"] = item_to_group.get(id(item), "")
        writer.writerow(row)
    return output.getvalue()


def cut_list_to_grouped_text(cutlist: dict) -> str:
    """Pretty-print cut list grouped by material/thickness."""
    groups = group_cut_list(cutlist)
    lines = [
        f"Cut List: {cutlist.get('name', 'Cut List')} (grouped)",
        f"Generated: {cutlist.get('generated_at', '')}",
        "=" * 72,
    ]
    total_qty = 0
    for gkey in sorted(groups.keys()):
        items = groups[gkey]
        lines.append(f"\n{gkey}")
        lines.append("-" * 72)
        lines.append(f"{'Qty':>4}  {'Name':<20}  {'Size (W x D x H)':<24}")
        lines.append("-" * 72)
        gqty = 0
        for it in items:
            qty = it.get("quantity", 1)
            gqty += qty
            name = (it.get("name") or "")[:20]
            sz = it.get("size") or {}
            if sz and sz.get("width") is not None:
                size_str = f"{sz.get('width', 0):.1f} x {sz.get('depth', 0):.1f} x {sz.get('height', 0):.1f}"
            else:
                size_str = "(no geometry)"
            lines.append(f"{qty:>4}  {name:<20}  {size_str:<24}")
        lines.append(f"  Subtotal quantity: {gqty}")
        total_qty += gqty
    lines.append("=" * 72)
    lines.append(f"Total unique parts: {len(cutlist.get('items', []))}")
    lines.append(f"Total quantity: {total_qty}")
    lines.append(f"Groups: {len(groups)}")
    return "\n".join(lines)


def cut_list_to_text(cutlist: dict) -> str:
    """Pretty-print a cut list as a simple text table (for logs / output/)."""
    lines = [
        f"Cut List: {cutlist.get('name', 'Cut List')}",
        f"Generated: {cutlist.get('generated_at', '')}",
        "-" * 72,
        f"{'Qty':>4}  {'Name':<20}  {'Material':<22}  {'Size (W x D x H)':<24}",
        "-" * 72,
    ]
    for it in cutlist.get("items", []):
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
    lines.append(f"Total unique parts: {len(cutlist.get('items', []))}")
    total_qty = sum(it.get("quantity", 1) for it in cutlist.get("items", []))
    lines.append(f"Total quantity: {total_qty}")
    return "\n".join(lines)


class CutList:
    """Thin wrapper around a validated cut-list document."""

    def __init__(self, data: dict):
        validate_cutlist_data(data)
        self.data = data

    @classmethod
    def from_parts(
        cls,
        parts: Union[Part, Sequence[Part]],
        material_store: Optional[MaterialStore] = None,
        quantities: Optional[Dict[str, int]] = None,
        name: str = "Cut List",
    ) -> "CutList":
        data = generate_cut_list(parts, material_store, quantities, name)
        return cls(data)

    def to_dict(self) -> dict:
        return dict(self.data)

    def to_text(self) -> str:
        return cut_list_to_text(self.data)

    def to_grouped_text(self) -> str:
        return cut_list_to_grouped_text(self.data)

    def to_csv(self, include_groups: bool = False) -> str:
        return cut_list_to_csv(self.data, include_groups=include_groups)

    def groups(self, by: str = "material_thickness") -> dict:
        return group_cut_list(self.data, by=by)

    def __repr__(self) -> str:
        return f"<CutList name={self.data.get('name')!r} items={len(self.data.get('items', []))}>"
