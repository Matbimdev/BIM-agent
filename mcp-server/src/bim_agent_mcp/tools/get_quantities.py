"""Herramienta 3: metrado agregado. Contrato en docs/02-contrato-herramientas.md."""
from typing import Any

from ..revit_client import RevitError
from .common import envelope

GROUPS = ("type", "level", "phase")
METRICS = ("count", "length", "area", "volume")
_NATURAL = {
    "OST_Floors": "area", "OST_Roofs": "area", "OST_Ceilings": "area", "OST_Walls": "area",
    "OST_StructuralFraming": "length", "OST_StructuralColumns": "volume", "OST_StructuralFoundation": "volume",
}
_CRITERIA = {
    "count": "Conteo de instancias",
    "length": "Parametro de instancia Length o longitud de curva",
    "area": "Area calculada del elemento hospedador (HOST_AREA_COMPUTED)",
    "volume": "Volumen calculado del elemento (HOST_VOLUME_COMPUTED)",
}


def validate(group_by: list[str], metric: str | None) -> None:
    invalid = [group for group in group_by if group not in GROUPS]
    if invalid or len(group_by) > 2:
        raise RevitError("InvalidGroup", "group_by no es valido.", f"Usa hasta 2 de: {', '.join(GROUPS)}.")
    if metric is not None and metric not in METRICS:
        raise RevitError("InvalidMetric", f"La metrica '{metric}' no es valida.", f"Usa: {', '.join(METRICS)}.")


def _quantity(value: float, unit: str | None) -> dict[str, Any] | None:
    return {"value": round(value, 3), "unit": unit} if unit else None


def normalize(raw: dict[str, Any], group_by: list[str], metric: str | None = None,
              limit: int | None = None) -> dict[str, Any]:
    chosen = metric or _NATURAL.get(raw["built_in"], "count")
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    unit = None
    total_value = 0.0
    without_value = 0
    for element in raw["elements"]:
        key = tuple(element[group] for group in group_by)
        entry = groups.setdefault(key, {"count": 0, "value": 0.0, "without_value": 0})
        entry["count"] += 1
        if chosen == "count":
            continue
        measured = element.get(chosen)
        if measured is None:
            entry["without_value"] += 1
            without_value += 1
            continue
        unit = measured["unit"]
        entry["value"] += measured["value"]
        total_value += measured["value"]
    data = [{"group": dict(zip(group_by, key)), "count": entry["count"],
             "quantity": _quantity(entry["value"], unit), "elements_without_value": entry["without_value"]}
            for key, entry in sorted(groups.items())]
    return {
        **envelope(data, limit),
        "category": raw["category"],
        "metric": chosen,
        "grand_total": {"count": len(raw["elements"]), "quantity": _quantity(total_value, unit)},
        "elements_without_value": without_value,
        "criterion": f"{_CRITERIA[chosen]}. Incluye todas las fases; sin filtro de demolicion.",
    }
