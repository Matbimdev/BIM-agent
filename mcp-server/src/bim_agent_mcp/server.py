"""Registro FastMCP de las herramientas de BIM Agent."""
from typing import Any

from mcp.server.fastmcp import FastMCP

from .revit_client import RevitClient, RevitError
from .session import Session
from .tools import audit_families as families
from .tools import audit_links_coordinates as links
from .tools import get_quantities as quantities
from .tools import query_elements as queries
from .tools import audit_naming as naming
from .tools import audit_parameters as parameters
from .tools import export_report as report
from .tools import get_sheets_and_views as sheets_views
from .tools.common import compile_regex
from .tools import get_model_overview as overview
from .tools import get_warnings as warnings

mcp = FastMCP("bim-agent")
client = RevitClient()
session = Session()


def _load_overview(include_links: bool = True) -> dict[str, Any]:
    args = {"include_links": include_links}
    raw = client.post("overview", args)
    session.record("get_model_overview", args, raw)
    return overview.normalize(raw)


@mcp.tool()
def get_model_overview(include_links: bool = True) -> dict[str, Any]:
    """Radiografia del modelo de Revit abierto: proyecto, unidades, worksharing, conteo por
    categoria, niveles, fases, worksets y vinculos. Llamala primero en cada sesion. Solo lectura."""
    try:
        return _load_overview(include_links)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def get_warnings(severity: str | None = None, top: int = 20, sample_per_group: int = 5) -> dict[str, Any]:
    """Warnings del modelo agrupados por descripcion y severidad, con UniqueId de muestra y
    densidad por 1000 elementos. Devuelve los grupos mas frecuentes. Solo lectura."""
    try:
        args = {"severity": severity, "top": top, "sample_per_group": sample_per_group}
        raw = client.post("warnings")
        session.record("get_warnings", args, raw)
        if "get_model_overview" not in session.results:
            _load_overview()
        elements_total = overview.normalize(session.results["get_model_overview"])["elements_total"]
        return warnings.normalize(raw, elements_total, severity, top, sample_per_group)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def get_sheets_and_views(include_unplaced: bool = True, view_types: list[str] | None = None,
                         limit: int | None = None) -> dict[str, Any]:
    """Planos con vistas colocadas y revision actual, y vistas de trabajo sin colocar en un plano.
    view_types filtra por tipo de vista, por ejemplo FloorPlan o Section. Solo lectura."""
    try:
        args = {"include_unplaced": include_unplaced, "view_types": view_types, "limit": limit}
        raw = client.post("sheets_views")
        session.record("get_sheets_and_views", args, raw)
        return sheets_views.normalize(raw, include_unplaced, view_types, limit)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def audit_families(checks: list[str] | None = None, type_count_threshold: int = 30,
                   limit: int | None = None) -> dict[str, Any]:
    """Audita familias: in_place, unused, duplicated y type_count. Los duplicados son posibles
    coincidencias de nombre que el usuario debe confirmar. Solo lectura."""
    try:
        args = {"checks": checks, "type_count_threshold": type_count_threshold, "limit": limit}
        raw = client.post("families")
        session.record("audit_families", args, raw)
        return families.normalize(raw, checks, type_count_threshold, limit)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def audit_naming(target: str, pattern: str, rule_text: str, category: str | None = None,
                 limit: int | None = None) -> dict[str, Any]:
    """Verifica nombres contra una expresion regular derivada del BEP. target: families, types,
    views, sheets, sheet_numbers o levels. Antes de llamarla, muestra el patron al usuario y pide
    que lo confirme. Solo lectura."""
    try:
        compiled = compile_regex(pattern)
        naming.validate_target(target)
        args = {"target": target, "pattern": pattern, "rule_text": rule_text, "category": category}
        raw = client.post("names", {"target": target})
        session.record("audit_naming", args, raw)
        session.add_rule_sheet(f"naming|{target}|{pattern}|{category}", "Nombres",
                               naming.rows(raw, compiled, rule_text, category))
        return naming.normalize(raw, target, compiled, rule_text, category, limit)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def audit_parameters(category: str, required: list[str] | None = None, rules: list[dict[str, Any]] | None = None,
                     limit: int | None = None) -> dict[str, Any]:
    """Revisa parametros en los elementos de una categoria, buscando en instancia y tipo. required
    lista los obligatorios; rules admite {"param": ..., "allowed": [...]} o {"param": ..., "regex": ...}.
    Solo lectura."""
    try:
        required, rules = required or [], rules or []
        for rule in rules:
            if "regex" in rule:
                compile_regex(rule["regex"])
        wanted = parameters.fields(required, rules)
        args = {"category": category, "required": required, "rules": rules}
        raw = client.post("elements", {"category": category, "fields": wanted})
        session.record("audit_parameters", args, raw)
        session.add_rule_sheet(f"parameters|{category}|{wanted}", "Parametros",
                               parameters.rows(raw, category, required, rules))
        return parameters.normalize(raw, required, rules, limit)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def audit_links_coordinates(include_cad: bool = True, max_distance_km: float = 10) -> dict[str, Any]:
    """Diagnostica puntos base, vinculos RVT e IFC y CAD: carga, fijacion, CAD importado y distancia
    al origen interno. No evalua coordenadas compartidas. Solo lectura."""
    try:
        args = {"include_cad": include_cad, "max_distance_km": max_distance_km}
        raw = client.post("links_coordinates")
        session.record("audit_links_coordinates", args, raw)
        return links.normalize(raw, include_cad, max_distance_km)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def query_elements(category: str, level: str | None = None, type_name: str | None = None,
                   filters: list[dict[str, Any]] | None = None, fields: list[str] | None = None,
                   include_type_params: bool = True, limit: int = 100) -> dict[str, Any]:
    """Busca elementos de una categoria y lee sus parametros. filters admite {"param", "op", "value"},
    con op eq, neq, contains, empty, not_empty, gt o lt. limit maximo 500. Solo lectura."""
    try:
        filters, fields = filters or [], fields or []
        queries.validate(filters)
        wanted = queries.requested(filters, fields)
        raw = client.post("elements", {"category": category, "fields": wanted})
        session.record("query_elements", {"category": category, "level": level, "fields": fields}, raw)
        return queries.normalize(raw, level, type_name, filters, fields, include_type_params, limit)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def get_quantities(category: str, group_by: list[str] | None = None, metric: str | None = None,
                   limit: int | None = None) -> dict[str, Any]:
    """Metrado agregado por type, level o phase (maximo 2). metric: count, length, area o volume; si
    se omite usa la natural de la categoria. Usa estos totales sin recalcularlos. Solo lectura."""
    try:
        group_by = group_by or []
        quantities.validate(group_by, metric)
        raw = client.post("quantities", {"category": category})
        session.record("get_quantities", {"category": category, "group_by": group_by, "metric": metric}, raw)
        return quantities.normalize(raw, group_by, metric, limit)
    except RevitError as err:
        return err.to_dict()


@mcp.tool()
def export_report(sections: list[str] | None = None, path: str | None = None) -> dict[str, Any]:
    """Genera el Excel de auditoria con las herramientas ya ejecutadas en la sesion y calcula el
    score de salud. Secciones: warnings, families, naming, parameters, links, sheets_views. Ejecuta
    antes get_model_overview y las auditorias pedidas. No consulta Revit; declara lo que falta."""
    try:
        return report.build(session, sections, path)
    except RevitError as err:
        return err.to_dict()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
