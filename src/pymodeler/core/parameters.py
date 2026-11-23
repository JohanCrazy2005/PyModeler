"""User Parameter / Variable store for parametric CAD.

Named parameters can be referenced by sketch dimensions (and later features).
Supports simple numeric values and basic arithmetic expressions that reference other parameters.
"""

from __future__ import annotations

import ast
import json
import operator
import uuid
from pathlib import Path
import math
from typing import Any, Callable, Dict, List, Optional

import jsonschema
from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"
_PARAMETER_SCHEMA_PATH = _SCHEMA_DIR / "parameter.schema.json"

with open(_PARAMETER_SCHEMA_PATH, encoding="utf-8") as f:
    PARAMETER_SCHEMA = json.load(f)

_PARAMETER_VALIDATOR = Draft202012Validator(PARAMETER_SCHEMA)


class ParameterValidationError(ValueError):
    """Raised when parameter data fails schema validation."""


class ParameterEvaluationError(ValueError):
    """Raised when an expression cannot be evaluated."""


def validate_parameter_data(data: dict) -> None:
    """Validate a dict against the ParameterStore JSON Schema."""
    errors = sorted(_PARAMETER_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if errors:
        messages = [f"{list(e.path)}: {e.message}" for e in errors]
        raise ParameterValidationError("Parameter schema validation failed:\n" + "\n".join(messages))


# Safe operators for expression evaluation
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe math functions (CAD-style: trig takes degrees by default)
_FUNCS: Dict[str, Callable[..., float]] = {
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
    "atan2": lambda y, x: math.degrees(math.atan2(y, x)),
    "sqrt": math.sqrt,
    "abs": abs,
    "min": min,
    "max": max,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "exp": math.exp,
    "log": math.log,  # natural log; log10 available as log10
    "log10": math.log10,
    "hypot": math.hypot,
    "pow": math.pow,
    # Unit conversion helpers (numeric, assuming base unit is mm for length)
    "in_to_mm": lambda x: x * 25.4,
    "mm_to_in": lambda x: x / 25.4,
    "deg_to_rad": math.radians,
    "rad_to_deg": math.degrees,
    # Explicit radians versions of trig
    "sin_rad": math.sin,
    "cos_rad": math.cos,
    "tan_rad": math.tan,
}

# Built-in constants
_CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "PI": math.pi,
    "Pi": math.pi,
    "e": math.e,
    "E": math.e,
}

# Length unit suffixes -> conversion factor to millimeters (base unit)
# Case-insensitive; optional space between number and unit.
_LENGTH_UNITS: Dict[str, float] = {
    "mm": 1.0,
    "millimeter": 1.0,
    "millimeters": 1.0,
    "cm": 10.0,
    "centimeter": 10.0,
    "centimeters": 10.0,
    "m": 1000.0,
    "meter": 1000.0,
    "meters": 1000.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
    "ft": 304.8,
    "foot": 304.8,
    "feet": 304.8,
}

import re

_UNIT_SUFFIX_RE = re.compile(
    r"(?P<num>\d*\.?\d+)\s*(?P<unit>mm|millimeter|millimeters|cm|centimeter|centimeters|"
    r"m|meter|meters|in|inch|inches|ft|foot|feet)\b",
    re.IGNORECASE,
)


def _expand_unit_suffixes(expression: str) -> str:
    """Replace numeric unit suffixes (e.g. '2 in', '10mm') with pure mm numeric literals.

    Base unit is millimeters. Unknown or non-length suffixes are left unchanged
    (and will typically fail later if they are invalid tokens).
    """
    def repl(m: re.Match) -> str:
        num = float(m.group("num"))
        unit = m.group("unit").lower()
        factor = _LENGTH_UNITS.get(unit)
        if factor is None:
            return m.group(0)
        mm_value = num * factor
        # Emit a clean numeric literal
        return f"{mm_value:.10g}"

    return _UNIT_SUFFIX_RE.sub(repl, expression)


def _eval_node(node: ast.AST, names: Dict[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        if node.id not in names:
            raise ParameterEvaluationError(f"Unknown parameter: {node.id}")
        return float(names[node.id])
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, names)
        right = _eval_node(node.right, names)
        op = _OPS.get(type(node.op))
        if op is None:
            raise ParameterEvaluationError(f"Unsupported operator: {type(node.op).__name__}")
        return float(op(left, right))
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, names)
        op = _OPS.get(type(node.op))
        if op is None:
            raise ParameterEvaluationError(f"Unsupported unary operator: {type(node.op).__name__}")
        return float(op(operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ParameterEvaluationError("Only simple function names are supported")
        fname = node.func.id
        if fname not in _FUNCS:
            raise ParameterEvaluationError(f"Unknown function: {fname}")
        args = [_eval_node(arg, names) for arg in node.args]
        try:
            return float(_FUNCS[fname](*args))
        except Exception as e:
            raise ParameterEvaluationError(f"Error calling {fname}: {e}") from e
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, names)
    raise ParameterEvaluationError(f"Unsupported expression node: {type(node).__name__}")


class ParameterStore:
    """Schema-compliant store of named user parameters."""

    def __init__(
        self,
        name: str = "Parameters",
        parameters: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
        id: Optional[str] = None,
    ):
        self.id = id or f"params_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.parameters: List[dict] = parameters or []
        self.metadata = metadata or {}
        self.validate()

    def to_dict(self) -> dict:
        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "parameters": self.parameters,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    def validate(self) -> None:
        validate_parameter_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "ParameterStore":
        validate_parameter_data(data)
        return cls(
            name=data.get("name", "Parameters"),
            parameters=data.get("parameters", []),
            metadata=data.get("metadata"),
            id=data.get("id"),
        )

    def __repr__(self) -> str:
        return f"<ParameterStore id={self.id!r} name={self.name!r} count={len(self.parameters)}>"

    # --- CRUD ---

    def add(
        self,
        name: str,
        value: Optional[float] = None,
        expression: Optional[str] = None,
        unit: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        if self.get(name) is not None:
            raise ValueError(f"Parameter '{name}' already exists")
        param: dict[str, Any] = {"name": name}
        if value is not None:
            param["value"] = float(value)
        if expression is not None:
            param["expression"] = expression
        if unit is not None:
            param["unit"] = unit
        if comment is not None:
            param["comment"] = comment
        self.parameters.append(param)
        self.validate()

    def update(
        self,
        name: str,
        value: Optional[float] = None,
        expression: Optional[str] = None,
        unit: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        param = self.get(name)
        if param is None:
            raise ValueError(f"Parameter '{name}' not found")
        if value is not None:
            param["value"] = float(value)
        if expression is not None:
            param["expression"] = expression
        if unit is not None:
            param["unit"] = unit
        if comment is not None:
            param["comment"] = comment
        self.validate()

    def remove(self, name: str) -> None:
        self.parameters = [p for p in self.parameters if p["name"] != name]
        self.validate()

    def get(self, name: str) -> Optional[dict]:
        for p in self.parameters:
            if p["name"] == name:
                return p
        return None

    def names(self) -> List[str]:
        return [p["name"] for p in self.parameters]

    # --- Evaluation ---

    def evaluate(self, name: str, _seen: Optional[set] = None) -> float:
        """Evaluate a parameter to a float, resolving expressions and named references.

        Cycles are detected. Expressions support numbers, identifiers, + - * / ** (),
        common math functions (sin/cos/tan in degrees, sqrt, abs, min/max, etc.),
        constants (pi, e), and simple unit helpers (in_to_mm, mm_to_in, deg_to_rad).
        """
        if _seen is None:
            _seen = set()
        if name in _seen:
            raise ParameterEvaluationError(f"Circular reference involving '{name}'")
        param = self.get(name)
        if param is None:
            raise ParameterEvaluationError(f"Unknown parameter: {name}")

        _seen.add(name)

        expr = param.get("expression")
        if expr is not None and str(expr).strip():
            expr_str = _expand_unit_suffixes(str(expr).strip())
            try:
                tree = ast.parse(expr_str, mode="eval")
            except SyntaxError as e:
                raise ParameterEvaluationError(f"Invalid expression for '{name}': {e}") from e

            def resolve_name(n: str) -> float:
                if n == name:
                    raise ParameterEvaluationError(f"Circular reference involving '{name}'")
                return self.evaluate(n, _seen.copy())

            result = self._eval_with_resolver(tree, resolve_name)
            return float(result)

        if "value" in param:
            return float(param["value"])
        raise ParameterEvaluationError(f"Parameter '{name}' has neither expression nor value")

    def _eval_with_resolver(self, node: ast.AST, resolver) -> float:
        if isinstance(node, ast.Expression):
            return self._eval_with_resolver(node.body, resolver)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id in _CONSTANTS:
                return _CONSTANTS[node.id]
            return float(resolver(node.id))
        if isinstance(node, ast.BinOp):
            left = self._eval_with_resolver(node.left, resolver)
            right = self._eval_with_resolver(node.right, resolver)
            op = _OPS.get(type(node.op))
            if op is None:
                raise ParameterEvaluationError(f"Unsupported operator: {type(node.op).__name__}")
            return float(op(left, right))
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_with_resolver(node.operand, resolver)
            op = _OPS.get(type(node.op))
            if op is None:
                raise ParameterEvaluationError(f"Unsupported unary operator")
            return float(op(operand))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ParameterEvaluationError("Only simple function names are supported")
            fname = node.func.id
            if fname not in _FUNCS:
                raise ParameterEvaluationError(f"Unknown function: {fname}")
            args = [self._eval_with_resolver(arg, resolver) for arg in node.args]
            try:
                return float(_FUNCS[fname](*args))
            except Exception as e:
                raise ParameterEvaluationError(f"Error calling {fname}: {e}") from e
        raise ParameterEvaluationError(f"Unsupported expression node: {type(node).__name__}")

    def evaluate_all(self) -> Dict[str, float]:
        """Evaluate every parameter (useful for debugging / UI)."""
        return {p["name"]: self.evaluate(p["name"]) for p in self.parameters}

    def evaluate_expression(self, expression: str) -> float:
        """Evaluate a free-form arithmetic expression using current parameter values.

        Supports numbers, parameter names, + - * / ** (), parentheses, unary +/-, 
        math functions (sin/cos/tan in degrees by default, sqrt, abs, min, max, ...),
        constants (pi, e), unit conversion helpers (in_to_mm, mm_to_in, ...),
        and numeric unit suffixes (e.g. `2 in`, `10mm`, `1.5 ft`) which are
        converted to millimeters before evaluation. Base unit is mm.
        Parameter references are resolved via evaluate (with cycle detection).
        """
        expr = str(expression).strip()
        if not expr:
            raise ParameterEvaluationError("Empty expression")
        expr = _expand_unit_suffixes(expr)
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as e:
            raise ParameterEvaluationError(f"Invalid expression: {e}") from e

        def resolve_name(n: str) -> float:
            return self.evaluate(n)

        return float(self._eval_with_resolver(tree, resolve_name))
