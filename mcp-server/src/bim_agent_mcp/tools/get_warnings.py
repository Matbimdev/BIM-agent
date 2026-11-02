"""Herramienta 5: warnings agrupados. Contrato en docs/02-contrato-herramientas.md."""
from typing import Any


def group(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa por descripcion y severidad, con los mas frecuentes primero."""
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for warning in warnings:
        key = (warning["description"], warning["severity"])
        entry = groups.setdefault(
            key, {"description": key[0], "severity": key[1], "count": 0, "elements": []})
        entry["count"] += 1
        entry["elements"].extend(warning["elements"])
    return sorted(groups.values(), key=lambda g: (-g["count"], g["description"]))


def _samples(elements: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Muestra sin repetidos: unique_id para otras llamadas, element_id para Select by ID en Revit."""
    unique = {element["unique_id"]: element for element in elements}
    return [
        {key: element[key] for key in ("unique_id", "element_id", "name", "category", "level")}
        for element in unique.values()
    ][:limit]


def per_thousand(warning_count: int, elements_total: int) -> float | None:
    return round(warning_count * 1000 / elements_total, 1) if elements_total else None


def normalize(raw: dict[str, Any], elements_total: int, severity: str | None = None,
              top: int = 20, sample_per_group: int = 5) -> dict[str, Any]:
    warnings = raw["warnings"]
    selected = warnings
    if severity:
        selected = [w for w in warnings if w["severity"].lower() == severity.lower()]
    groups = group(selected)
    top = max(top, 1)
    sample_per_group = max(sample_per_group, 0)
    returned = groups[:top]
    truncated = len(groups) > len(returned)
    return {
        "total": len(selected),
        "groups_total": len(groups),
        "returned": len(returned),
        "truncated": truncated,
        "hint": "Aumenta top para ver los grupos omitidos." if truncated else "",
        "warnings_por_1000_elementos": per_thousand(len(warnings), elements_total),
        "data": [
            {"description": g["description"], "severity": g["severity"], "count": g["count"],
             "sample_elements": _samples(g["elements"], sample_per_group)}
            for g in returned
        ],
    }
