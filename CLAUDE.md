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

## 6. Estado (2026-11-14)

Roadmap y siguientes pasos en `docs/04-roadmap.md`. Empezar cada sesion por ahi.

F0 a F5 cerradas. Las 10 herramientas responden con Snowdon en Revit 2026 y 2027 (1.450
elementos de modelo, warnings 2, 12 planos). Contrastadas contra Revit el 11/11: metrado de
Floors igual a la tabla de planificacion (CA-04), familias no usadas con Select All Instances y
Purge (CP-06), vinculos sin fijar y CAD importado (CP-09). Panel `BIMAgent.tab` con
Iniciar/Detener, Estado y Seleccionar. 87 tests sin Revit.

Siguiente: F6, validacion. No hay prueba con otros usuarios: se valida con 2 o 3 casos de uso
reales del autor reproducidos sobre Snowdon y cronometrados contra una linea base manual, y el
sesgo de autor se declara como limitacion.

Limitaciones declaradas: no se audita el posicionamiento por coordenadas compartidas; el metrado
incluye todas las fases; `audit_families` opina sobre 83 de 185 familias y calla sobre las que
se usan desde un tipo; el score de salud es una heuristica provisional sin calibrar y sus
conteos de familias y vistas no escalan con el tamano del modelo.

Puertos: pyRevit da a cada Revit abierto el siguiente puerto libre; `revit_client.py` busca el
bridge del 48884 al 48890 y usa el que tenga documento abierto. `scripts/smoke.py` solo usa 48884.

Datos: solo Snowdon en fixtures, Excel de ejemplo y capturas; nada de modelos de clientes.
Nunca versionar `Encuesta.csv`, `entregables/`, `rubricas/` ni `.rvt`.

Leccion IronPython: `.Name` falla en tipos como `FamilySymbol` o `RevitLinkType` (cualquier
`ElementType`); usar `serializers.element_name` (`Element.Name.GetValue`). En el panel, bajo
CPython (Revit 2027) `pyrevit.forms` no existe: usar `TaskDialog`. Los tests sin Revit no
detectan estos errores: validar cada endpoint nuevo con `scripts/smoke.py` o por MCP contra el
modelo.
