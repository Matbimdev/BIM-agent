"""Herramienta 1: radiografia del modelo. Contrato en docs/02-contrato-herramientas.md."""
from typing import Any

CATEGORY_LIMIT = 60

_UNITS = {
    "meters": "m", "decimeters": "dm", "centimeters": "cm", "millimeters": "mm",
    "feet": "ft", "inches": "in", "feetFractionalInches": "ft-in",
    "fractionalInches": "in", "metersCentimeters": "m-cm",
    "squareMeters": "m2", "squareCentimeters": "cm2", "squareMillimeters": "mm2",
    "squareFeet": "ft2", "squareInches": "in2", "acres": "ac", "hectares": "ha",
    "cubicMeters": "m3", "cubicCentimeters": "cm3", "cubicMillimeters": "mm3",
    "liters": "L", "cubicFeet": "ft3", "cubicInches": "in3", "cubicYards": "yd3",
}


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Convierte la respuesta cruda del bridge en la salida del contrato."""
    project = dict(raw["project"])
    project["units"] = {key: _UNITS.get(token, token) for key, token in project["units"].items()}

    categories = sorted(raw["categories"], key=lambda c: (-c["count"], c["category"]))
    total = len(categories)
    returned = categories[:CATEGORY_LIMIT]
    truncated = total > len(returned)

    levels = sorted(raw["levels"], key=lambda level: level["elevation"]["value"])
    levels = [
        {"name": level["name"],
         "elevation": {"value": round(level["elevation"]["value"], 3),
                       "unit": level["elevation"]["unit"]}}
        for level in levels
    ]

    result = {
        "project": project,
        "categories": returned,
        "categories_meta": {
            "truncated": truncated,
            "total": total,
            "returned": len(returned),
            "hint": "Filtra con query_elements para consultar una categoria omitida." if truncated else "",
        },
        "levels": levels,
        "phases": raw["phases"],
        "worksets": raw["worksets"],
        "elements_total": sum(c["count"] for c in categories),
    }
    if "links" in raw:
        result["links"] = raw["links"]
    return result
