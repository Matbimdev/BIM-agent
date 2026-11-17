# BIM Agent - Ficha técnica

Autor y titular del código: Luis Mateo López Ríos. Contacto: lmateolopezr@gmail.com.

Agente que conversa con un modelo de Revit abierto mediante un servidor MCP. Lee, mide, audita y
reporta; nunca modifica el modelo. El usuario pregunta en lenguaje natural en Claude, el agente
consulta el modelo, aplica las reglas de auditoría y entrega un Excel con hallazgos trazables a
cada elemento por su UniqueId.

## 1. Acceso

| Recurso | Dónde |
|---|---|
| Código | https://github.com/Matbimdev/BIM-agent |
| Video de respaldo (demo del flujo principal) | https://drive.google.com/file/d/1tYXNdJOJGT_ft9GL7w2tXlGk007zZ82k/view?usp=sharing |
| Anexo: casos de uso cronometrados (manual contra agente) | https://drive.google.com/file/d/12MmK6Pq9MNsmJqYx-pT0gmnrsvQyFba1/view?usp=sharing |

Repositorio público para su evaluación.
Licencia propietaria: ver `LICENSE`.

Estructura del repositorio:

| Carpeta | Contenido |
|---|---|
| `revit-bridge/` | Extensión pyRevit que corre dentro de Revit (IronPython 2.7). Expone rutas HTTP de solo lectura en `localhost:48884` y el panel `BIMAgent` |
| `mcp-server/` | Servidor MCP (Python 3.11, FastMCP): las 10 herramientas, validación, unidades, truncado, Excel y score |
| `docs/` | Arquitectura, contrato de herramientas (fuente de verdad), decisiones (ADR), roadmap y validación |
| `samples/payloads/` | Respuestas reales del bridge sobre Snowdon y datos sintéticos para los tests |
| `scripts/` | Registro en Claude Desktop y prueba de humo contra Revit |

## 2. Dependencias

Requisitos previos:

| Requisito | Versión probada | Origen |
|---|---|---|
| Windows | 10 u 11 | - |
| Autodesk Revit | 2026 y 2027 | Licencia de Autodesk |
| pyRevit | 7, con Routes activo | https://github.com/pyrevitlabs/pyRevit/releases |
| uv (gestor de Python) | 0.5 o superior | https://docs.astral.sh/uv/getting-started/installation/ |
| Claude Desktop o Claude Code | Actual, con una cuenta de Claude | https://claude.ai/download |

Python 3.11 y las librerías del servidor (`mcp`, `httpx`, `openpyxl`) las instala `uv` en un
entorno propio dentro de `mcp-server/.venv`. El bridge no usa librerías externas.

## 3. Instalación

1. Descarga el repositorio en GitHub con `Code` > `Download ZIP` (no hace falta Git) y
   descomprímelo en una carpeta sin acentos. Esa carpeta no se mueve después de instalar; si se
   mueve, hay que repetir los pasos 2 a 4.
2. En una consola, dentro de esa carpeta, crea el entorno del servidor MCP:
   `uv sync --directory mcp-server`
3. Registra la extensión en pyRevit y activa Routes:
   `pyrevit extensions paths add "%CD%\revit-bridge"` y `pyrevit configs routes enable`
4. Agrega `bim-agent` a Claude Desktop. El script guarda antes una copia `.bak` y no toca los
   demás servidores: `uv run --directory mcp-server python ..\scripts\register_claude_desktop.py`.
   Con Claude Code, al abrir esta carpeta toma la configuración de `.mcp.json`.
5. Abre Revit y pulsa `Reload` en la pestaña pyRevit. Aparece la pestaña `BIMAgent`.
6. Cierra Claude Desktop por completo y vuelve a abrirlo.

Los pasos 2 a 4 se pueden repetir sin riesgo: si ya estaban hechos, quedan igual.

## 4. Uso

1. Abre el modelo en Revit. En la pestaña `BIMAgent`, `Estado` muestra el bridge, el puerto, el
   modelo y la versión. `Iniciar/Detener` prende o apaga el bridge.
2. En Claude, pregunta en lenguaje natural. Ejemplos:
   - "Dame una radiografía del modelo abierto."
   - "Audita el modelo: warnings, familias, vistas sin plano, nombres de niveles, material de
     las vigas y vínculos. Después genera el Excel."
   - "¿Qué vigas del nivel L2 TOS tienen un Cut Length mayor a 18 pies?"
3. El Excel se guarda en `Documentos\BIMAgent\`. Tiene una hoja de resumen con el score, una hoja
   por regla y una de trazabilidad.
4. Para ver un hallazgo en el modelo, copia sus UniqueId de la columna del Excel y pulsa
   `Seleccionar` en el panel.

Las 10 herramientas. El código de cada una está en `mcp-server/src/bim_agent_mcp/tools/`, en un
archivo con su mismo nombre:

| # | Herramienta | Código | Qué responde |
|---|---|---|---|
| 1 | `get_model_overview` | `tools/get_model_overview.py` | Proyecto, unidades, conteo por categoría, niveles, fases, worksets y vínculos. Va primero |
| 2 | `query_elements` | `tools/query_elements.py` | Elementos por categoría, nivel, tipo o valor de parámetro |
| 3 | `get_quantities` | `tools/get_quantities.py` | Metrado por tipo, nivel o fase, con unidad |
| 4 | `get_sheets_and_views` | `tools/get_sheets_and_views.py` | Planos, vistas colocadas y vistas sin colocar |
| 5 | `get_warnings` | `tools/get_warnings.py` | Warnings agrupados por descripción, con elementos de muestra |
| 6 | `audit_families` | `tools/audit_families.py` | Familias in-place, sin usar, duplicadas o con exceso de tipos |
| 7 | `audit_naming` | `tools/audit_naming.py` | Nombres contra un patrón derivado del BEP; el agente lo muestra y el usuario lo confirma |
| 8 | `audit_parameters` | `tools/audit_parameters.py` | Parámetros obligatorios faltantes, vacíos o inválidos |
| 9 | `audit_links_coordinates` | `tools/audit_links_coordinates.py` | Vínculos RVT/IFC/CAD y punto base |
| 10 | `export_report` | `tools/export_report.py` | Excel con hallazgos, trazabilidad y score de salud |

Las 10 se registran en `mcp-server/src/bim_agent_mcp/server.py`. La parte que lee Revit está en
`revit-bridge/BIMAgent.extension/lib/bim_agent_bridge/handlers/`; la correspondencia de cada
herramienta con su archivo del bridge está en `docs/01-arquitectura.md`, sección 3. El contrato
de entradas y salidas está en `docs/02-contrato-herramientas.md`.

## 5. Datos

- Modelo de prueba: Snowdon Towers Sample Structural, de los modelos de muestra que Autodesk
  publica con Revit. No se versiona (`*.rvt` está en `.gitignore`).
- `samples/payloads/`: respuestas reales del bridge sobre Snowdon (metrado, familias, vínculos)
  y datos sintéticos. Los nombres de los DWG de prueba se reemplazaron por etiquetas genéricas.
- No hay datos de clientes en el repositorio.
- Qué sale de la máquina: el bridge solo escucha en `localhost`. Lo que las herramientas
  devuelven (nombres, conteos, parámetros pedidos, UniqueId) llega al modelo de lenguaje de
  Claude como parte de la conversación. El archivo `.rvt` no se envía.

## 6. Restricciones

- Solo lectura: el bridge no abre transacciones. Verificado con `Document.IsModified` al final de
  una sesión de auditoría.
- Puertos: pyRevit da a cada Revit abierto el siguiente puerto libre. El servidor busca el bridge
  del 48884 al 48890 y usa el que tenga un modelo abierto. `scripts/smoke.py` solo usa el 48884.
- Seguridad: cada pedido al bridge lleva un token local guardado en `%APPDATA%\BIMAgent\token`.
- Respuestas truncadas: ninguna herramienta devuelve el modelo entero. `query_elements` corta en
  100 elementos (máximo 500), las auditorías, el metrado y las vistas en 200, `get_warnings` en
  20 grupos y `get_model_overview` en 60 categorías. Toda respuesta cortada lo declara con
  `truncated`, `total`, `returned` y un `hint` que dice cómo ver el resto.
- No audita el posicionamiento por coordenadas compartidas.
- El metrado suma todas las fases.
- La regla de familias sin usar (FAM-002) opina sobre 83 de las 185 familias de Snowdon. No dice
  nada de las 102 que se usan desde un tipo (formas de armadura, perfiles, cabezas de nivel);
  para esas, el complemento es Purge Unused. Las demás reglas de familias (in-place, duplicadas
  y exceso de tipos) revisan las 185.
- El score de salud es una heurística provisional sin calibrar: sirve para comparar un mismo
  modelo en el tiempo, no modelos distintos.
- `get_model_overview` cuenta cada vínculo RVT y cada DWG como elemento de modelo.
- Requiere una cuenta de Claude; el costo de uso depende del plan del usuario.

## 7. Reproducción

Pruebas sin Revit (90 tests, sobre los payloads de `samples/payloads/`):

```
cd mcp-server
uv run pytest
```

Prueba contra un modelo abierto, con el bridge en el puerto 48884, desde la carpeta del
repositorio:

```
uv run --directory mcp-server python ..\scripts\smoke.py overview
```

Validación: `docs/09-f6-validacion.md` describe el modelo, las 15 reglas, el método manual de
cada una, los tiempos (55:05 a mano contra 38 s del agente), los casos de uso y CA-01 a CA-06.
Para repetirla, abre Snowdon con los mismos vínculos y DWG y sigue ese protocolo.
