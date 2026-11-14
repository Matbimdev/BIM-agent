# BIM Agent - Ficha tecnica

Autor y titular del codigo: Luis Mateo Lopez Rios. Contacto: lmateolopezr@gmail.com.

Agente que conversa con un modelo de Revit abierto mediante un servidor MCP. Lee, mide, audita y
reporta; nunca modifica el modelo. El usuario pregunta en lenguaje natural en Claude, el agente
consulta el modelo, aplica las reglas de auditoria y entrega un Excel con hallazgos trazables a
cada elemento por su UniqueId.

## 1. Acceso

| Recurso | Donde |
|---|---|
| Codigo | https://github.com/Matbimdev/BIM-agent |
| Video de respaldo (demo de 3 a 5 min) | _enlace pendiente_ |
| Anexo: casos de uso cronometrados | _enlace pendiente_ |

Repositorio privado; el autor lo abre como publico el dia de la entrega, para su evaluacion.
Licencia propietaria: ver `LICENSE`.

Estructura del repositorio:

| Carpeta | Contenido |
|---|---|
| `revit-bridge/` | Extension pyRevit que corre dentro de Revit (IronPython 2.7). Expone rutas HTTP de solo lectura en `localhost:48884` y el panel `BIMAgent` |
| `mcp-server/` | Servidor MCP (Python 3.11, FastMCP): las 10 herramientas, validacion, unidades, truncado, Excel y score |
| `docs/` | Arquitectura, contrato de herramientas (fuente de verdad), decisiones (ADR), roadmap y validacion |
| `samples/payloads/` | Respuestas reales del bridge sobre Snowdon y datos sinteticos para los tests |
| `scripts/` | Registro en Claude Desktop, pruebas de humo contra Revit y utilidades |

## 2. Dependencias

Requisitos previos.

| Requisito | Version probada | Origen |
|---|---|---|
| Windows | 10 u 11 | - |
| Autodesk Revit | 2026 y 2027 | Licencia de Autodesk |
| pyRevit | 7, con Routes activo | https://github.com/pyrevitlabs/pyRevit/releases |
| uv (gestor de Python) | 0.5 o superior | https://docs.astral.sh/uv/getting-started/installation/ |
| Claude Desktop o Claude Code | Actual, con una cuenta de Claude | https://claude.ai/download |

Python 3.11 y las librerias del servidor (`mcp`, `httpx`, `openpyxl`) las instala `uv` en un
entorno propio dentro de `mcp-server/.venv`. El bridge no usa librerias externas.

## 3. Instalacion

1. Descarga el repositorio en GitHub con `Code` > `Download ZIP` (no hace falta Git) y
   descomprimelo en una carpeta sin acentos. Esa carpeta no se mueve despues de instalar; si se
   mueve, hay que repetir los pasos 2 a 4.
2. En una consola, dentro de esa carpeta, crea el entorno del servidor MCP:
   `uv sync --directory mcp-server`
3. Registra la extension en pyRevit y activa Routes:
   `pyrevit extensions paths add "%CD%\revit-bridge"` y `pyrevit configs routes enable`
4. Agrega `bim-agent` a Claude Desktop. El script guarda antes una copia `.bak` y no toca los
   demas servidores: `uv run --directory mcp-server python ..\scripts\register_claude_desktop.py`.
   Con Claude Code, al abrir esta carpeta toma la configuracion de `.mcp.json`.
5. Abre Revit y pulsa `Reload` en la pestana pyRevit. Aparece la pestana `BIMAgent`.
6. Cierra Claude Desktop por completo y vuelve a abrirlo.

Los pasos 2 a 4 se pueden repetir sin riesgo: si ya estaban hechos, quedan igual.

## 4. Uso

1. Abre el modelo en Revit. En la pestana `BIMAgent`, `Estado` muestra el bridge, el puerto, el
   modelo y la version. `Iniciar/Detener` prende o apaga el bridge.
2. En Claude, pregunta en lenguaje natural. Ejemplos:
   - "Dame una radiografia del modelo abierto."
   - "Audita el modelo: warnings, familias, vistas sin plano, nombres de niveles, material de
     las vigas y vinculos. Despues genera el Excel."
   - "Que vigas del nivel L2 TOS tienen un Cut Length mayor a 18 pies?"
3. El Excel se guarda en `Documentos\BIMAgent\`. Tiene una hoja de resumen con el score, una hoja
   por regla y una de trazabilidad.
4. Para ver un hallazgo en el modelo, copia sus UniqueId de la columna del Excel y pulsa
   `Seleccionar` en el panel.

Las 10 herramientas. El codigo de cada una esta en `mcp-server/src/bim_agent_mcp/tools/`, en un
archivo con su mismo nombre:

| # | Herramienta | Codigo | Que responde |
|---|---|---|---|
| 1 | `get_model_overview` | `tools/get_model_overview.py` | Proyecto, unidades, conteo por categoria, niveles, fases, worksets y vinculos. Va primero |
| 2 | `query_elements` | `tools/query_elements.py` | Elementos por categoria, nivel, tipo o valor de parametro |
| 3 | `get_quantities` | `tools/get_quantities.py` | Metrado por tipo, nivel o fase, con unidad |
| 4 | `get_sheets_and_views` | `tools/get_sheets_and_views.py` | Planos, vistas colocadas y vistas sin colocar |
| 5 | `get_warnings` | `tools/get_warnings.py` | Warnings agrupados por descripcion, con elementos de muestra |
| 6 | `audit_families` | `tools/audit_families.py` | Familias in-place, sin usar, duplicadas o con exceso de tipos |
| 7 | `audit_naming` | `tools/audit_naming.py` | Nombres contra un patron derivado del BEP; el agente lo muestra y el usuario lo confirma |
| 8 | `audit_parameters` | `tools/audit_parameters.py` | Parametros obligatorios faltantes, vacios o invalidos |
| 9 | `audit_links_coordinates` | `tools/audit_links_coordinates.py` | Vinculos RVT/IFC/CAD y punto base |
| 10 | `export_report` | `tools/export_report.py` | Excel con hallazgos, trazabilidad y score de salud |

Las 10 se registran en `mcp-server/src/bim_agent_mcp/server.py`. La parte que lee Revit esta en
`revit-bridge/BIMAgent.extension/lib/bim_agent_bridge/handlers/`; la correspondencia de cada
herramienta con su archivo del bridge esta en `docs/01-arquitectura.md`, seccion 3. El contrato
de entradas y salidas esta en `docs/02-contrato-herramientas.md`.

## 5. Datos

- Modelo de prueba: Snowdon Towers Sample Structural, de los modelos de muestra que Autodesk
  publica con Revit. No se versiona (`*.rvt` esta en `.gitignore`).
- `samples/payloads/`: respuestas reales del bridge sobre Snowdon (metrado, familias, vinculos)
  y datos sinteticos. Los nombres de los DWG de prueba se reemplazaron por etiquetas genericas.
- No hay datos de clientes en el repositorio.
- Que sale de la maquina: el bridge solo escucha en `localhost`. Lo que las herramientas
  devuelven (nombres, conteos, parametros pedidos, UniqueId) llega al modelo de lenguaje de
  Claude como parte de la conversacion. El archivo `.rvt` no se envia.

## 6. Restricciones

- Solo lectura: el bridge no abre transacciones. Verificado con `Document.IsModified` al final de
  una sesion de auditoria.
- Puertos: pyRevit da a cada Revit abierto el siguiente puerto libre. El servidor busca el bridge
  del 48884 al 48890 y usa el que tenga un modelo abierto. `scripts/smoke.py` solo usa el 48884.
- Seguridad: cada pedido al bridge lleva un token local guardado en `%APPDATA%\BIMAgent\token`.
- Respuestas truncadas: las listas se cortan en 100 o 200 elementos y lo declaran con
  `truncated`, `total` y `returned`.
- No audita el posicionamiento por coordenadas compartidas.
- El metrado suma todas las fases.
- `audit_families` opina sobre 83 de las 185 familias de Snowdon. No dice nada de las que se
  usan desde un tipo (perfiles, cabezas de nivel); para esas, el complemento es Purge Unused.
- El score de salud es una heuristica provisional sin calibrar: sirve para comparar un mismo
  modelo en el tiempo, no modelos distintos.
- `get_model_overview` cuenta cada vinculo RVT y cada DWG como elemento de modelo.
- Requiere una cuenta de Claude; el costo de uso depende del plan del usuario.

## 7. Reproduccion

Pruebas sin Revit (90 tests, sobre los payloads de `samples/payloads/`):

```
cd mcp-server
uv run pytest
```

Prueba contra un modelo abierto, con el bridge en el puerto 48884:

```
uv run --directory mcp-server python scripts/smoke.py overview
```

Validacion: `docs/09-f6-validacion.md` describe el modelo, las 15 reglas, el metodo manual de
cada una, los tiempos (55:05 a mano contra 38 s del agente), los casos de uso y CA-01 a CA-06.
Para repetirla, abre Snowdon con los mismos vinculos y DWG y sigue ese protocolo.
