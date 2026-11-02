"""Herramienta 2: busqueda de elementos y lectura de parametros."""
import difflib
from typing import Any

from ..revit_client import RevitError
from .common import envelope

OPERATORS = ("eq", "neq", "contains", "empty", "not_empty", "gt", "lt")
MAX_LIMIT = 500


def validate(filters: list[dict[str, Any]]) -> None:
    for item in filters:
        if item.get("op") not in OPERATORS or "param" not in item:
            raise RevitError("InvalidFilter", f"Filtro no valido: {item}.",
                             f"Usa {{'param': ..., 'op': ..., 'value': ...}} con op: {', '.join(OPERATORS)}.")
        if item["op"] in ("gt", "lt"):
            _number(item.get("value"), strict=True)


def requested(filters: list[dict[str, Any]], fields: list[str]) -> list[str]:
    return list(dict.fromkeys([*fields, *(item["param"] for item in filters)]))


def _number(value: Any, strict: bool = False) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        if strict:
            raise RevitError("InvalidFilter", f"El valor '{value}' debe ser numerico.",
                             "Para longitud, area y volumen usa m, m2 y m3.") from None
        return None


def _visible(state: dict[str, Any], include_type_params: bool) -> bool:
    return state["found"] and (include_type_params or state["source"] != "type")


def _text(state: dict[str, Any]) -> str:
    return (state.get("value") or "").strip() if state["has_value"] else ""


def _matches(state: dict[str, Any], rule: dict[str, Any], include_type_params: bool) -> bool:
    op = rule["op"]
    has_value = _visible(state, include_type_params) and bool(_text(state))
    if op == "empty":
        return not has_value
    if op == "not_empty":
        return has_value
    if not has_value:
        return op == "neq"
    text, expected = _text(state), str(rule.get("value", ""))
    if op in ("gt", "lt"):
        current = state["quantity"]["value"] if state.get("quantity") else _number(text)
        limit = float(rule["value"])
        return current is not None and (current > limit if op == "gt" else current < limit)
    equal = text.lower() == expected.lower()
    if state.get("quantity") and _number(expected) is not None:
        equal = abs(state["quantity"]["value"] - float(expected)) < 1e-6
    if op == "eq":
        return equal
    if op == "neq":
        return not equal
    return expected.lower() in text.lower()


def _check_parameters(raw: dict[str, Any], names: list[str]) -> None:
    elements = raw["elements"]
    for name in names:
        if elements and not any(element["params"][name]["found"] for element in elements):
            close = difflib.get_close_matches(name, raw.get("available_params", []), n=5, cutoff=0.4)
            raise RevitError("ParameterNotFound", f"El parametro '{name}' no existe en esta categoria.",
                             f"Parametros parecidos: {', '.join(close) or 'ninguno'}.")


def _value(state: dict[str, Any], include_type_params: bool) -> Any:
    if not _visible(state, include_type_params) or not state["has_value"]:
        return None
    return state.get("quantity") or state.get("value")


def normalize(raw: dict[str, Any], level: str | None, type_name: str | None, filters: list[dict[str, Any]],
              fields: list[str], include_type_params: bool = True, limit: int = 100) -> dict[str, Any]:
    _check_parameters(raw, requested(filters, fields))
    data = []
    for element in raw["elements"]:
        if level and element["level"].lower() != level.lower():
            continue
        if type_name and element["type"].lower() != type_name.lower():
            continue
        if not all(_matches(element["params"][rule["param"]], rule, include_type_params) for rule in filters):
            continue
        data.append({"unique_id": element["unique_id"], "element_id": int(element["element_id"]),
                     "category": element["category"], "family": element["family"], "type": element["type"],
                     "level": element["level"],
                     "params": {field: _value(element["params"][field], include_type_params) for field in fields}})
    return envelope(data, min(max(limit, 1), MAX_LIMIT), "Aumenta limit, maximo 500, o agrega filtros.")
