"""Herramienta 4: planos y vistas no colocadas. Contrato en docs/02-contrato-herramientas.md."""
import re
from typing import Any

from .. import config
from .common import envelope, rule_row

RULE_TEXT = "Toda vista de trabajo debe estar colocada en un plano"


def is_required(view: dict[str, Any]) -> bool:
    return view["view_type"] in config.REQUIRED_VIEW_TYPES


def unplaced(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Todas las vistas fuera de un plano, exigibles e informativas."""
    working = re.compile(config.WORKING_VIEW_PATTERN, re.IGNORECASE)
    views = [v for v in raw["views"] if not v["placed"] and not working.match(v["name"])]
    return sorted(views, key=lambda v: (v["view_type"], v["name"]))


def required_unplaced(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Solo las que la regla VIS-001 exige ver en un plano. Son las que van al reporte y al score."""
    return [v for v in unplaced(raw) if is_required(v)]


def normalize(raw: dict[str, Any], include_unplaced: bool = True,
              view_types: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
    sheets = [{key: sheet[key] for key in ("number", "name", "views_placed", "current_revision")}
              | {"unique_id": sheet["unique_id"], "element_id": int(sheet["element_id"])}
              for sheet in sorted(raw["sheets"], key=lambda s: s["number"])]
    result = {"sheets": envelope(sheets, limit)}
    if include_unplaced:
        wanted = {v.lower() for v in view_types} if view_types else None
        views = [{"name": v["name"], "view_type": v["view_type"], "required": is_required(v),
                  "unique_id": v["unique_id"], "element_id": int(v["element_id"])}
                 for v in unplaced(raw) if wanted is None or v["view_type"].lower() in wanted]
        result["unplaced_views"] = envelope(views, limit)
        required = sum(1 for v in views if v["required"])
        result["unplaced_summary"] = {"required": required, "informative": len(views) - required}
    return result


def rows(raw: dict[str, Any]) -> list[list[Any]]:
    return [rule_row("VIS-001", RULE_TEXT, {**v, "category": v["view_type"]}, "No colocada", "Colocada en un plano")
            for v in required_unplaced(raw)]
