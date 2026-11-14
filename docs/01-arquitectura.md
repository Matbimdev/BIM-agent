# Arquitectura

BIM Agent deja que una persona audite un modelo de Revit abierto conversando con Claude. El agente
lee, mide y reporta; no modifica el modelo (ADR-002).

## 1. Tres capas

```
Claude Desktop / Claude Code        El modelo de lenguaje: entiende el pedido, elige herramientas,
        |                           traduce reglas a parametros y redacta la respuesta.
        |  MCP por stdio
        v
mcp-server/   (Python 3.11)         Las 10 herramientas. Valida la entrada, agrega, convierte
        |                           unidades, trunca, genera el Excel y traduce errores.
        |  HTTP POST localhost:48884/bim-agent/<ruta>, JSON con token
        v
revit-bridge/ (pyRevit, IronPython)  Corre dentro de Revit. Solo extrae datos de la Revit API y
        |                           los serializa. Sin transacciones.
        v
Modelo .rvt abierto
```

Regla de diseno: toda la logica de negocio vive en `mcp-server`. El bridge solo entrega datos
crudos con un contrato JSON estable. Si el bridge se reemplaza por un add-in C# (ADR-001), el
servidor MCP no cambia.

## 2. Responsabilidades

| Parte | Archivo | Que hace |
|---|---|---|
| Registro de herramientas | `mcp-server/src/bim_agent_mcp/server.py` | Declara las 10 herramientas MCP y llama al bridge |
| Logica por herramienta | `mcp-server/src/bim_agent_mcp/tools/` | Un archivo por herramienta: reglas, agregacion, formato |
| Cliente HTTP | `mcp-server/src/bim_agent_mcp/revit_client.py` | Unico punto que habla con el bridge: token, puertos, tiempos de espera, errores |
| Sesion | `mcp-server/src/bim_agent_mcp/session.py` | Guarda los resultados de la sesion para que `export_report` arme el Excel sin volver a Revit |
| Configuracion | `mcp-server/src/bim_agent_mcp/config.py` | Puertos, tiempos, pesos del score, tipos de vista exigibles |
| Rutas del bridge | `revit-bridge/BIMAgent.extension/startup.py` | Registra las rutas en pyRevit Routes |
| Extraccion | `revit-bridge/.../lib/bim_agent_bridge/handlers/` | Un archivo por dominio: overview, warnings, vistas, familias, nombres, elementos, vinculos |
| Serializacion | `revit-bridge/.../lib/bim_agent_bridge/serializers.py` | Element a diccionario plano; conversion unica desde pies internos de Revit |
| Panel | `revit-bridge/BIMAgent.extension/BIMAgent.tab/` | Botones `Iniciar/Detener`, `Estado` y `Seleccionar` dentro de Revit |

## 3. Herramientas y rutas del bridge

| Herramienta | Ruta | Logica en el servidor |
|---|---|---|
| `get_model_overview` | `/overview` | Excluye categorias que no son de modelo, ordena y trunca |
| `query_elements` | `/elements` | Filtros por nivel, tipo y parametro (`eq`, `gt`, `empty`, ...) |
| `get_quantities` | `/quantities` | Agrupa por tipo, nivel o fase y suma con unidad |
| `get_sheets_and_views` | `/sheets_views` | Separa vistas exigibles de informativas (regla VIS-001) |
| `get_warnings` | `/warnings` | Agrupa por descripcion y calcula warnings por cada 1000 elementos |
| `audit_families` | `/families` | Reglas FAM-001 a FAM-004 |
| `audit_naming` | `/names` | Aplica el patron que el usuario confirmo |
| `audit_parameters` | `/elements` | Obligatorios faltantes, vacios o fuera de una lista o patron |
| `audit_links_coordinates` | `/links_coordinates` | Reglas VIN-001 a VIN-006 |
| `export_report` | ninguna | Excel con resumen, hoja por regla, trazabilidad y score; no consulta Revit |

Contrato completo de entradas y salidas: `docs/02-contrato-herramientas.md`.

## 4. Recorrido de un pedido

Ejemplo: "Que vigas del nivel L2 TOS tienen un Cut Length mayor a 18 pies?"

1. Claude elige `query_elements` y arma los argumentos: categoria Structural Framing, nivel
   L2 TOS, filtro `Cut Length` `gt` 5,486. Convierte los pies a metros porque el contrato
   trabaja en unidades del sistema metrico.
2. `mcp-server` valida el filtro y pide al bridge `/elements` con los campos necesarios.
3. El bridge lee los elementos con la Revit API, convierte las longitudes de pies a metros una
   sola vez y responde JSON con `UniqueId`, tipo, nivel y parametros.
4. `mcp-server` filtra, arma la respuesta con `{"value", "unit"}` y trunca a 100 con
   `truncated`, `total` y `hint`.
5. Claude redacta la respuesta: 28 vigas, por tipo.

## 5. Controles

| Control | Como se cumple |
|---|---|
| Solo lectura | El bridge no abre `Transaction`. Verificado con `Document.IsModified` al final de una auditoria |
| Acceso local | El bridge escucha solo en `localhost`. Cada pedido lleva un token de `%APPDATA%\BIMAgent\token` (ADR-006) |
| Tamano de respuesta | Toda lista se trunca y lo declara; nunca se devuelve el modelo entero |
| Unidades | Cada magnitud viaja como `{"value": 12.5, "unit": "m2"}`; la conversion se hace solo en `serializers.py` |
| Referencias estables | Los hallazgos usan `UniqueId`; `ElementId` es solo para mostrar |
| Varias sesiones de Revit | `revit_client.py` busca el bridge del puerto 48884 al 48890 y usa el que tenga un modelo abierto |
| Errores utiles | Sin modelo, categoria inexistente o parametro mal escrito: la respuesta dice que hacer y sugiere nombres parecidos |
| Revision humana | `audit_naming` exige mostrar el patron al usuario antes de auditar |

## 6. Pruebas

- 90 tests sin Revit (`mcp-server/tests/`) sobre respuestas reales del bridge guardadas en
  `samples/payloads/`.
- Pruebas contra Revit 2026 y 2027 con Snowdon Towers: `scripts/smoke.py` y la validacion de
  `docs/09-f6-validacion.md`.
