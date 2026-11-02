"""Registro FastMCP de las herramientas de BIM Agent."""
from typing import Any

from mcp.server.fastmcp import FastMCP

from .revit_client import RevitClient, RevitError
from .session import Session
from .tools import export_report as report
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
def export_report(sections: list[str] | None = None, path: str | None = None) -> dict[str, Any]:
    """Genera el Excel de auditoria con las herramientas ya ejecutadas en la sesion y calcula el
    score de salud. Secciones: warnings, families, naming, parameters, links, sheets_views. No
    consulta Revit; declara las secciones y componentes sin datos."""
    try:
        return report.build(session, sections, path)
    except RevitError as err:
        return err.to_dict()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
