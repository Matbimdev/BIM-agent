"""Herramienta 6: riesgo de familias. Contrato en docs/02-contrato-herramientas.md."""
import re
from typing import Any

from .common import envelope, rule_row

CHECKS = ("in_place", "unused", "duplicated", "type_count")
RULES = {
    "in_place": ("FAM-001", "No debe haber familias in-place"),
    "unused": ("FAM-002", "No debe haber familias sin instancias colocadas"),
    "duplicated": ("FAM-003", "No debe haber familias duplicadas por sufijo de copia o numerico"),
    "type_count": ("FAM-004", "La familia no debe exceder el umbral de tipos"),
}
# Los perfiles se usan desde tipos o barridos, no como instancias: no se pueden juzgar por conteo.
_NOT_COUNTABLE = {"OST_ProfileFamilies"}
_COPY_SUFFIX = re.compile(r"[\s_-]*(?:(?:copia|copy)[\s_-]*\d{0,2}|\d{1,2})$", re.IGNORECASE)


def _duplicates(families: list[dict[str, Any]]) -> dict[str, str]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for family in families:
        base = _COPY_SUFFIX.sub("", family["family"]) or family["family"]
        groups.setdefault((family["category"], base.lower()), []).append(family)
    found = {}
    for group in groups.values():
        if len(group) > 1:
            names = sorted(f["family"] for f in group)
            for family in group:
                found[family["unique_id"]] = ", ".join(n for n in names if n != family["family"])
    return found


def findings(raw: dict[str, Any], type_count_threshold: int = 30) -> dict[str, list[dict[str, Any]]]:
    families = raw["families"]
    duplicates = _duplicates(families)
    result = {check: [] for check in CHECKS}
    for family in sorted(families, key=lambda f: (f["category"], f["family"])):
        base = {"family": family["family"], "category": family["category"], "instances": family["instances"],
                "unique_id": family["unique_id"], "element_id": int(family["element_id"])}
        if family["in_place"]:
            result["in_place"].append({**base, "check": "in_place", "detail": "Familia in-place"})
        if family["instances"] == 0 and family["built_in"] not in _NOT_COUNTABLE:
            result["unused"].append({**base, "check": "unused", "detail": "Sin instancias colocadas"})
        if family["unique_id"] in duplicates:
            result["duplicated"].append(
                {**base, "check": "duplicated", "detail": f"Posible duplicado de: {duplicates[family['unique_id']]}"})
        if family["types"] > type_count_threshold:
            result["type_count"].append({**base, "check": "type_count", "detail": f"{family['types']} tipos"})
    return result


def normalize(raw: dict[str, Any], checks: list[str] | None = None, type_count_threshold: int = 30,
              limit: int | None = None) -> dict[str, Any]:
    found = findings(raw, type_count_threshold)
    selected = [check for check in CHECKS if not checks or check in checks]
    data = [item for check in selected for item in found[check]]
    return {**envelope(data, limit), "checked": len(raw["families"]),
            "summary": {check: len(found[check]) for check in selected}}


def rows(raw: dict[str, Any]) -> list[list[Any]]:
    result = []
    for check, items in findings(raw).items():
        rule, text = RULES[check]
        for item in items:
            result.append(rule_row(rule, text, {**item, "name": item["family"]}, item["detail"], "Sin hallazgo"))
    return result
