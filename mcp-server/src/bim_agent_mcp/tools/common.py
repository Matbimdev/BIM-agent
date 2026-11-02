"""Utilidades compartidas por las herramientas de auditoria."""
import re
from typing import Any

from .. import config
from ..revit_client import RevitError


def compile_regex(pattern: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise RevitError("InvalidRegex", f"La expresion regular no es valida: {exc}.",
                         "Corrige el patron y confirmalo con el usuario.") from exc


def envelope(data: list[Any], limit: int | None = None, hint: str = "Aumenta limit para ver el resto.") -> dict[str, Any]:
    limit = config.RESULT_LIMIT if limit is None else max(limit, 1)
    returned = data[:limit]
    truncated = len(data) > len(returned)
    return {"data": returned, "truncated": truncated, "total": len(data),
            "returned": len(returned), "hint": hint if truncated else ""}


def rule_row(rule: str, text: str, item: dict[str, Any], found: Any, expected: Any) -> list[Any]:
    return [rule, text, item.get("unique_id", ""), int(item.get("element_id") or 0) or "",
            item.get("name", ""), item.get("category", ""), item.get("level", ""), found, expected]
