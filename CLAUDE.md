# BIM Agent

Agente BIM que conversa con un modelo de Revit abierto a traves de un servidor MCP.
El agente no modela: lee, mide, audita y reporta.

## 1. Arquitectura

Tres capas, contrato JSON estable entre ellas:

```
Claude (Desktop / Code)
        | MCP  stdio
mcp-server/        Python 3.11 + FastMCP.  Define las 10 tools, valida input,
        |          normaliza salida, cachea, y traduce errores a lenguaje util.
        | HTTP  localhost:48884  (JSON)
revit-bridge/      Extension pyRevit con Routes. Corre DENTRO de Revit (IronPython).
        |          Solo lectura de la Revit API. Sin transacciones.
Modelo .rvt abierto
```

Regla dura: toda logica de negocio (agregacion, formato, unidades, texto para el LLM)
vive en `mcp-server`. El bridge solo extrae datos crudos de la Revit API y los serializa.
Asi el dia que el bridge migre a un add-in C#, el MCP no cambia.

## 2. Estructura

```
CLAUDE.md
docs/
  01-arquitectura.md         diagramas y flujo de datos
  02-contrato-herramientas.md   fuente de verdad de las 10 tools (schemas I/O)
  03-decisiones.md           ADRs cortos, uno por decision irreversible
  04-roadmap.md              fases y criterios de salida
revit-bridge/
  BIMAgent.extension/
    startup.py               registro de rutas pyRevit Routes
    lib/bim_agent_bridge/
      routes.py              un endpoint por tool, thin
      handlers/              extraccion Revit API, un archivo por dominio
      serializers.py         Element -> dict plano y estable
      errors.py              errores tipados (NoDocument, CategoryNotFound, ...)
    BIMAgent.tab/              botones opcionales (start/stop server, health)
mcp-server/
  pyproject.toml
  src/bim_agent_mcp/
    server.py                registro FastMCP
    config.py                host, puerto, timeouts, feature flags
    revit_client.py          unico punto que habla HTTP con el bridge
    schemas.py               pydantic models de entrada y salida
    tools/                   un archivo por tool
  tests/                     tests contra payloads de samples/, sin Revit
samples/
  models/                    .rvt de prueba (no versionar los pesados)
  payloads/                  respuestas JSON reales del bridge, fixtures de test
scripts/                     deploy de la extension, arranque local, smoke tests
```

## 3. Las 10 herramientas

Presupuesto cerrado. Agregar una obliga a quitar otra, y eso es un ADR en `docs/03-decisiones.md`.

| # | Tool | Que responde |
|---|------|--------------|
| 1 | `get_model_overview` | Radiografia: datos de proyecto, unidades, version, worksharing, conteo por categoria, niveles, fases, worksets, vinculos. Punto de entrada obligatorio |
| 2 | `query_elements` | Filtro por categoria, nivel, tipo o valor de parametro, y lectura de parametros de instancia y tipo. Devuelve UniqueId, truncado a 100 |
| 3 | `get_quantities` | Metrados agregados por tipo, nivel o fase, con unidad y criterio de medicion |
| 4 | `get_sheets_and_views` | Planos, vistas colocadas, vistas no colocadas |
| 5 | `get_warnings` | Warnings agrupados por descripcion y severidad, con elementos de muestra |
| 6 | `audit_families` | Familias in-place, no usadas, duplicadas, con exceso de tipos |
| 7 | `audit_naming` | Nombres de familias, tipos, vistas, planos o niveles contra un regex derivado del BEP |
| 8 | `audit_parameters` | Parametros obligatorios faltantes, vacios o invalidos |
| 9 | `audit_links_coordinates` | Punto base, punto de reconocimiento, estado de vinculos RVT/IFC/CAD |
| 10 | `export_report` | Excel con resumen, hoja por regla y trazabilidad; calcula el score de salud |

Contrato completo en `docs/02-contrato-herramientas.md`. Lista revisada en ADR-005 (2026-10-18).

## 4. Reglas de implementacion

Solo lectura. El bridge no abre `Transaction` ni modifica el documento. Cualquier
propuesta de escritura se discute antes, es cambio de alcance.

Descubrimiento antes de detalle. `get_model_overview` es barato y orienta al agente.
Las tools de detalle exigen filtros y nunca devuelven el modelo entero.

Presupuesto de tokens por respuesta. Toda tool trunca y avisa: devuelve
`{"data": [...], "truncated": true, "total": 4210, "returned": 200, "hint": "..."}`.
Nunca se devuelve una lista de miles de elementos.

Unidades explicitas. Cada magnitud viaja como `{"value": 12.5, "unit": "m2"}`.
La conversion desde pies internos de Revit se hace una sola vez, en `serializers.py`.

IDs estables. Se usa `UniqueId` para referenciar entre llamadas, `ElementId` solo para mostrar.

Errores utiles. Si no hay documento abierto, si la categoria no existe, si el modelo esta
en un estado raro, la respuesta explica que hacer, no lanza un stack trace.

Entorno de desarrollo: Revit 2026, pyRevit 7, modelo Snowdon Towers Sample Structural.

IronPython 2.7 en el bridge. Sin f-strings, sin type hints, sin dataclasses, sin
librerias externas. En `mcp-server` si hay Python 3.11 moderno.

## 5. Flujo de trabajo con Claude Code

Antes de escribir codigo de una tool, actualizar su contrato en `docs/02-contrato-herramientas.md`.
El contrato manda sobre el codigo.

Debugging: hipotesis primero, parche minimo, sin volcar archivos completos en el chat.

Cada tool nueva se entrega con un fixture en `samples/payloads/` y un test que corre sin Revit.

Verificacion manual de una tool: `scripts/smoke.py <tool> <args>` contra un modelo abierto,
antes de darla por cerrada.

## 6. Estado

Fase 0 cerrada: contratos escritos (2026-10-18). Fase 1 en curso. Fechas: Hito 2 20/10/2026, Hito 3 12/11/2026.

### Pendientes al 2026-10-18

- Hito 2 (vence 20/10 23:59): integrar encuesta ampliada (marcador [PENDIENTE] en Tabla 1 de `docs/08-hito02-plan.md`, sin pasar de 12 paginas), regenerar PDF con `scripts/build.sh`, subir PDF y link a Classroom. Prototipo ya publico (v6, 2026-10-18): las 10 tools en el recorrido, reglas en lenguaje claro.
- F1 vertical slice: `BIMAgent.extension` con `/health` y `/overview`, `mcp-server` con `get_model_overview`. Modelo de prueba: Snowdon Towers Sample Structural.
- ADR-006 aceptado (2026-10-18): endpoints POST, token en el cuerpo JSON, API `bim-agent`. `/health` probado en Revit 2026 con Snowdon (200 con token, 401 sin token) el 2026-10-18. Correr con `scripts/2_smoke.bat`.
- Laboratorio aparte (no es el proyecto): extension de referencia mcp-server-for-revit-python en %APPDATA%\pyRevit\Extensions, funcionando. Requiere parche local en pyRevit-Master `routes/server/server.py` (original en server.py.orig) para reenviar cabeceras; se pierde si se actualiza pyRevit.
- Leccion del laboratorio: con herramientas atomicas el agente recurre a ejecutar codigo; parametros se resuelven en cascada instancia -> tipo.
