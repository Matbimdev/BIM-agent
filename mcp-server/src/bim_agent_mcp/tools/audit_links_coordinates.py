"""Herramienta 9: vinculos y coordenadas. Contrato en docs/02-contrato-herramientas.md."""
from typing import Any

from .common import rule_row

RULES = {
    "link_loaded": ("VIN-001", "Todo vinculo debe estar cargado"),
    "link_path": ("VIN-002", "Todo vinculo debe encontrarse en su ruta"),
    "link_pinned": ("VIN-003", "Todo vinculo debe estar fijado"),
    "cad_imported": ("VIN-004", "Los CAD deben vincularse, no importarse"),
    "cad_pinned": ("VIN-005", "Todo CAD vinculado debe estar fijado"),
    "base_point_distance": ("VIN-006", "El punto base debe estar cerca del origen interno"),
}


def findings(raw: dict[str, Any], include_cad: bool = True, max_distance_km: float = 10) -> list[dict[str, Any]]:
    found = []

    def add(rule: str, item: dict[str, Any], detail: str) -> None:
        found.append({"rule": rule, "target": item.get("name", ""), "detail": detail,
                      "unique_id": item.get("unique_id", ""), "element_id": item.get("element_id")})

    for link in raw["links"]:
        if not link["path_found"]:
            add("link_path", link, f"Vinculo no encontrado en su ruta ({link['status']})")
        elif not link["loaded"]:
            add("link_loaded", link, f"Vinculo sin cargar ({link['status']})")
        if link["instances"] and not link["pinned"]:
            add("link_pinned", link, "Vinculo sin fijar")
    if include_cad:
        for cad in raw["cad"]:
            if not cad["linked"]:
                add("cad_imported", cad, "CAD importado")
            elif not cad["pinned"]:
                add("cad_pinned", cad, "CAD vinculado sin fijar")
    base = raw.get("base_point")
    if base and base["distance_from_origin"]["value"] > max_distance_km * 1000:
        distance = base["distance_from_origin"]["value"] / 1000
        add("base_point_distance", {"name": "Punto base del proyecto"},
            f"A {distance:.2f} km del origen interno, maximo {max_distance_km} km")
    return found


def normalize(raw: dict[str, Any], include_cad: bool = True, max_distance_km: float = 10) -> dict[str, Any]:
    links = [{"name": link["name"], "kind": link["kind"], "loaded": link["loaded"], "pinned": link["pinned"],
              "positioning": "not_evaluated", "path_found": link["path_found"], "unique_id": link["unique_id"],
              "element_id": int(link["element_id"])} for link in raw["links"]]
    result = {"base_point": raw.get("base_point"), "survey_point": raw.get("survey_point"), "links": links,
              "findings": [{**item, "element_id": int(item["element_id"]) if item["element_id"] else None}
                           for item in findings(raw, include_cad, max_distance_km)],
              "not_evaluated": ["Posicionamiento por coordenadas compartidas"]}
    if include_cad:
        result["cad"] = [{**cad, "element_id": int(cad["element_id"])} for cad in raw["cad"]]
    return result


def rows(raw: dict[str, Any]) -> list[list[Any]]:
    result = []
    for item in findings(raw):
        rule, text = RULES[item["rule"]]
        result.append(rule_row(rule, text, {**item, "name": item["target"]}, item["detail"], "Sin hallazgo"))
    return result
