# BIM Agent

Agente que conversa con un modelo de Revit abierto mediante un servidor MCP. Lee, mide, audita y
reporta; no modifica el modelo. Repositorio privado, ver `LICENSE`.

## Componentes

- `revit-bridge/`: extension pyRevit (IronPython 2.7) con rutas de solo lectura en `localhost:48884`.
- `mcp-server/`: servidor MCP (Python 3.11, FastMCP) con la logica, los limites y el reporte Excel.
- `docs/`: arquitectura, contrato de herramientas, decisiones y roadmap.
- `samples/payloads/`: datos de prueba sinteticos y del modelo de muestra Snowdon Towers.

## Instalacion en Windows

Requisitos: Revit 2026, pyRevit 7 con Routes activo, `uv` y Claude Desktop.

1. Ejecuta `scripts\1_register.bat` y recarga pyRevit.
2. Ejecuta `scripts\4_register_claude_desktop.bat`, o agrega el servidor a
   `claude_desktop_config.json`, y reinicia Claude Desktop.
3. Con un modelo abierto, prueba `py -3 scripts\smoke.py overview`.

## Pruebas sin Revit

```
cd mcp-server
uv run pytest
```
