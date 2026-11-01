"""Registro FastMCP de las herramientas de BIM Agent."""
from typing import Any

from mcp.server.fastmcp import FastMCP

from .revit_client import RevitClient, RevitError
from .tools import get_model_overview as overview

mcp = FastMCP("bim-agent")
client = RevitClient()


@mcp.tool()
def get_model_overview(include_links: bool = True) -> dict[str, Any]:
    """Radiografia del modelo de Revit abierto: proyecto, unidades, worksharing, conteo por
    categoria, niveles, fases, worksets y vinculos. Llamala primero en cada sesion. Solo lectura."""
    try:
        return overview.normalize(client.post("overview", {"include_links": include_links}))
    except RevitError as err:
        return err.to_dict()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
