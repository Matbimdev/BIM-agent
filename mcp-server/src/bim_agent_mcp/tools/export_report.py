"""Herramienta 10: reporte Excel y score de salud. No llama al bridge."""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from .. import config
from ..revit_client import RevitError
from ..session import Session
from . import audit_families, get_sheets_and_views
from .get_model_overview import normalize
from .get_warnings import group, per_thousand

SECTION_SOURCES = {
    "warnings": "get_warnings", "families": "audit_families", "naming": "audit_naming",
    "parameters": "audit_parameters", "links": "audit_links_coordinates",
    "sheets_views": "get_sheets_and_views",
}
RULE_COLUMNS = ["Regla", "Texto de la regla", "UniqueId", "ElementId", "Elemento", "Categoria",
                "Nivel", "Valor encontrado", "Valor esperado"]


def _elements_total(overview: dict[str, Any]) -> int:
    return normalize(overview)["elements_total"]


def _measurements(session: Session) -> dict[str, float]:
    found: dict[str, float] = {}
    overview = session.results.get("get_model_overview")
    if overview and "links" in overview:
        found["cad_importados"] = overview["links"]["cad_imported"]
    warnings = session.results.get("get_warnings")
    if overview and warnings:
        rate = per_thousand(len(warnings["warnings"]), _elements_total(overview))
        if rate is not None:
            found["warnings_por_1000"] = rate
    families = session.results.get("audit_families")
    if families:
        result = audit_families.findings(families)
        found["familias_in_place"] = len(result["in_place"])
        found["familias_no_usadas"] = len(result["unused"])
    views = session.results.get("get_sheets_and_views")
    if views:
        found["vistas_no_colocadas"] = len(get_sheets_and_views.unplaced(views))
    return found


def health_score(measurements: dict[str, float]) -> dict[str, Any]:
    components = []
    missing = []
    earned = available = 0.0
    for name, rule in config.HEALTH_COMPONENTS.items():
        if name not in measurements:
            missing.append(name)
            continue
        value = measurements[name]
        points = rule["weight"] * 100 * max(0.0, 1 - value / rule["limit"])
        earned += points
        available += rule["weight"] * 100
        components.append({"name": name, "value": value, "weight": rule["weight"], "points": round(points, 1)})
    return {
        "value": round(earned / available * 100) if available else None,
        "max": 100,
        "complete": not missing,
        "components": components,
        "missing_components": missing,
    }


def _text(sheet: Worksheet, row: int, column: int, value: Any) -> None:
    """Escribe siempre como dato: un texto del modelo que empiece con = no se ejecuta en Excel."""
    cell = sheet.cell(row=row, column=column, value=value)
    if isinstance(value, str):
        cell.data_type = "s"


def _append(sheet: Worksheet, values: list[Any]) -> None:
    row = sheet.max_row + 1 if sheet.max_row > 1 or sheet["A1"].value is not None else 1
    for column, value in enumerate(values, start=1):
        _text(sheet, row, column, value)


def _header(sheet: Worksheet, values: list[Any]) -> None:
    _append(sheet, values)
    for cell in sheet[sheet.max_row]:
        cell.font = Font(bold=True)


def _rule_sheet(book: Workbook, title: str, rows: list[list[Any]]) -> None:
    sheet = book.create_sheet(title)
    _header(sheet, RULE_COLUMNS)
    sheet.freeze_panes = "A2"
    for row in rows:
        _append(sheet, row)


def _warnings_sheet(book: Workbook, raw: dict[str, Any]) -> int:
    sheet = book.create_sheet("Warnings")
    _header(sheet, RULE_COLUMNS)
    sheet.freeze_panes = "A2"
    count = 0
    for index, entry in enumerate(group(raw["warnings"]), start=1):
        rule = f"WARN-{index:03d}"
        for element in entry["elements"] or [{}]:
            _append(sheet, [rule, entry["description"], element.get("unique_id", ""),
                            element.get("element_id", ""), element.get("name", ""),
                            element.get("category", ""), element.get("level", ""),
                            entry["severity"], "Sin warning"])
            count += 1
    return count


def _output_path(path: str | None, model: str, now: datetime) -> Path:
    if path:
        target = Path(path)
        return target if target.suffix.lower() == ".xlsx" else target.with_suffix(".xlsx")
    safe = re.sub(r"[^\w.-]+", "_", model).strip("_") or "modelo"
    return config.REPORT_DIR / f"BIMAgent_Auditoria_{safe}_{now:%Y%m%d_%H%M%S}.xlsx"


def build(session: Session, sections: list[str] | None = None, path: str | None = None) -> dict[str, Any]:
    requested = sections or list(SECTION_SOURCES)
    unknown = [s for s in requested if s not in SECTION_SOURCES]
    if unknown:
        raise RevitError("InvalidSection", f"Secciones no validas: {', '.join(unknown)}.",
                         f"Usa solo: {', '.join(SECTION_SOURCES)}.")
    included = [s for s in requested if SECTION_SOURCES[s] in session.results]
    missing = [s for s in requested if s not in included]
    if not included:
        raise RevitError("NoAuditData", "No hay auditorias ejecutadas en esta sesion para reportar.",
                         "Ejecuta primero las herramientas de auditoria, por ejemplo get_warnings.")

    now = datetime.now().astimezone()
    score = health_score(_measurements(session))
    overview = session.results.get("get_model_overview", {})
    project = overview.get("project", {})
    model = project.get("name") or session.document or "modelo"

    book = Workbook()
    summary = book.active
    summary.title = "Resumen"
    summary.column_dimensions["A"].width = 30
    summary.column_dimensions["B"].width = 50
    _append(summary, ["Modelo", model])
    _append(summary, ["Numero", project.get("number", "")])
    _append(summary, ["Version de Revit", project.get("revit_version", "")])
    _append(summary, ["Fecha", now.strftime("%Y-%m-%d %H:%M")])
    status = "" if score["complete"] else " (parcial)"
    _append(summary, ["Score de salud", f"{score['value']}/100{status}" if score["value"] is not None else "No disponible"])
    _append(summary, ["Componentes sin datos", ", ".join(score["missing_components"])])
    _append(summary, ["Secciones sin ejecutar", ", ".join(missing)])
    _append(summary, [])
    _header(summary, ["Componente", "Valor", "Peso", "Puntos"])
    for component in score["components"]:
        _append(summary, [component["name"], component["value"], component["weight"], component["points"]])

    if "warnings" in included:
        _warnings_sheet(book, session.results["get_warnings"])
    if "families" in included:
        _rule_sheet(book, "Familias", audit_families.rows(session.results["audit_families"]))
    if "sheets_views" in included:
        _rule_sheet(book, "Vistas no colocadas", get_sheets_and_views.rows(session.results["get_sheets_and_views"]))
    counters: dict[str, int] = {}
    for sheet in session.rule_sheets.values():
        counters[sheet["prefix"]] = counters.get(sheet["prefix"], 0) + 1
        section = "naming" if sheet["prefix"] == "Nombres" else "parameters"
        if section in included:
            _rule_sheet(book, f"{sheet['prefix']} {counters[sheet['prefix']]}", sheet["rows"])

    trace = book.create_sheet("Trazabilidad")
    _header(trace, ["Herramienta", "Argumentos", "Hora"])
    for call in session.calls:
        _append(trace, [call["tool"], json.dumps(call["args"], ensure_ascii=False), call["time"].strftime("%Y-%m-%d %H:%M:%S")])

    target = _output_path(path, model, now)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        book.save(target)
    except OSError as exc:
        raise RevitError("ReportNotSaved", f"No se pudo guardar el reporte en {target}.",
                         "Cierra el archivo si esta abierto en Excel o indica otra ruta.") from exc
    return {"path": str(target), "sheets": book.sheetnames, "health_score": score,
            "sections_included": included, "sections_missing": missing}
