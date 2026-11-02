# Contrato de herramientas

Fuente de verdad de las 10 herramientas de la v1. El contrato manda sobre el codigo.
Version 1.0, 2026-10-18. Lista revisada respecto del Hito 1, ver ADR-005 en `03-decisiones.md`.

## Convenciones comunes

Sobre de respuesta de toda herramienta que devuelve listas:

```json
{"data": [], "truncated": false, "total": 0, "returned": 0, "hint": ""}
```

Magnitudes siempre como `{"value": 12.5, "unit": "m2"}`. Conversion desde pies internos una sola vez, en `serializers.py`.
Elementos referenciados por `unique_id` (estable entre llamadas); `element_id` solo para mostrar al usuario.
Errores tipados, nunca stack trace: `NoDocument`, `BridgeUnavailable`, `Unauthorized`, `InternalError`, `CategoryNotFound`, `ParameterNotFound`, `InvalidRegex`, `Timeout`. Cada error trae `message` y `action` (que hacer).
Bridge: `POST http://localhost:48884/bim-agent/<endpoint>` con cuerpo `{"token": "...", "args": {...}}` (ADR-006). Solo lectura, sin `Transaction`.

## Resumen y trazabilidad

| # | Herramienta | Regla que audita | Requisito | Evidencia que la sustenta |
|---|---|---|---|---|
| 1 | `get_model_overview` | Ninguna, descubrimiento | RF-01 | Radiografia, unica capacidad elegida 3/3 |
| 2 | `query_elements` | La que el usuario formule como filtro | RF-02 | Busqueda combinada 1/3; encargos de lectura |
| 3 | `get_quantities` | Ninguna, metrado con criterio declarado | RF-03 | 32 encargos de metrados; 1/3 |
| 4 | `get_sheets_and_views` | Toda vista de trabajo debe estar en un plano | RF-04 | Vistas no colocadas 1/3; planos desactualizados |
| 5 | `get_warnings` | Warnings agrupados por tipo y severidad | RF-05 | Lo que se escapa (P1); 1/3 |
| 6 | `audit_families` | Sin in-place, sin no usadas, sin duplicadas | RF-06 | 15 encargos de salud de modelo; 1/3 |
| 7 | `audit_naming` | Nombres cumplen la convencion del BEP | RF-07 | 2/3 |
| 8 | `audit_parameters` | Parametros obligatorios presentes, llenos y validos | RF-08 | 2/3 |
| 9 | `audit_links_coordinates` | Vinculos cargados, fijados y en coordenadas compartidas | RF-09 | 2/3; 14 encargos de coordenadas |
| 10 | `export_report` | Consolida hallazgos y calcula score de salud | RF-10 | Reporte Excel 3/3 |

---

## 1. get_model_overview

Proposito: orientar al agente antes de cualquier detalle. Llamada obligatoria al inicio de la sesion. Absorbe a `get_project_info` del Hito 1.

Entrada: `include_links: bool = true`.

Salida:
```json
{
  "project": {"name": "", "number": "", "client": "", "address": "", "revit_version": "2026",
              "units": {"length": "m", "area": "m2", "volume": "m3"},
              "worksharing": true, "central_path": ""},
  "categories": [{"category": "Walls", "count": 1240}],
  "levels": [{"name": "N+0.00", "elevation": {"value": 0.0, "unit": "m"}}],
  "phases": ["Existente", "Nueva construccion"],
  "worksets": ["Arquitectura", "Vinculos"],
  "links": {"rvt": 3, "ifc": 1, "cad_linked": 4, "cad_imported": 2},
  "elements_total": 18450
}
```
Truncado: `categories` a 60 entradas ordenadas por conteo; `categories_meta` agrega `{"truncated", "total", "returned", "hint"}`. `elements_total` cuenta los elementos de modelo, aunque se trunque la lista. Se excluyen por `BuiltInCategory` las categorias que no son elementos del modelo (bocetos, materiales, planos, puntos base y similares); `excluded_non_model` declara `{"elements", "categories"}`. El bridge entrega `built_in` en cada categoria y `mcp-server` aplica la exclusion. `project.units` son las unidades de visualizacion del proyecto; cada magnitud declara su propia unidad.
Endpoint: `/overview`.

## 2. query_elements

Proposito: buscar elementos por criterios combinados y leer sus parametros. Fusiona `find_elements` y `get_element_parameters` del Hito 1.

Entrada:
```json
{"category": "Doors", "level": "N+0.00", "type_name": null,
 "filters": [{"param": "Fire Rating", "op": "empty"}],
 "fields": ["Mark", "Fire Rating", "Width"],
 "include_type_params": true, "limit": 100}
```
`op` admite `eq`, `neq`, `contains`, `empty`, `not_empty`, `gt`, `lt`. `limit` por defecto 100, maximo 500.

Salida: sobre comun con `data: [{"unique_id", "element_id", "category", "family", "type", "level", "params": {"Width": {"value": 0.9, "unit": "m"}}}]`.
Error: `ParameterNotFound` lista los parametros disponibles mas parecidos.
Endpoint: `/elements`.

## 3. get_quantities

Proposito: metrado agregado dentro de Revit; el modelo de lenguaje nunca suma.

Entrada: `{"category": "Floors", "group_by": ["type", "level"], "metric": "area"}`. `group_by` admite `type`, `level`, `phase` (maximo 2). `metric` admite `count`, `length`, `area`, `volume`; si se omite se elige el natural de la categoria.

Salida:
```json
{"data": [{"group": {"type": "Losa 20cm", "level": "N+3.00"}, "count": 12,
           "quantity": {"value": 412.6, "unit": "m2"}}],
 "total": {"count": 48, "quantity": {"value": 1650.4, "unit": "m2"}},
 "criterion": "Parametro de instancia Area (cara superior), fase Nueva construccion"}
```
Validacion: el total debe coincidir con una tabla de planificacion de Revit del mismo filtro (caso de prueba CP-03).
Endpoint: `/quantities`.

## 4. get_sheets_and_views

Proposito: inventario de planos y deteccion de vistas huerfanas.

Entrada: `{"include_unplaced": true, "view_types": ["FloorPlan", "Section"]}`.

Salida:
```json
{"sheets": {"total": 42, "data": [{"number": "A-101", "name": "Planta N+0.00", "views_placed": 3, "current_revision": "R02"}]},
 "unplaced_views": {"total": 27, "data": [{"name": "Corte 5", "view_type": "Section", "unique_id": ""}]}}
```
Regla: toda vista de trabajo debe estar colocada en un plano. Se excluyen plantillas, vistas de sistema y vistas cuyo nombre cumple el patron de trabajo configurado (por defecto prefijo `WIP` o `TRABAJO`).
Endpoint: `/sheets_views`.

## 5. get_warnings

Proposito: convertir la lista plana de warnings de Revit en grupos accionables.

Entrada: `{"severity": null, "top": 20, "sample_per_group": 5}`.

Salida:
```json
{"total": 812, "groups_total": 37, "returned": 20, "truncated": true, "hint": "",
 "warnings_por_1000_elementos": 44.0,
 "data": [{"description": "Highlighted walls overlap...", "severity": "Warning", "count": 214,
           "sample_elements": ["<unique_id>"]}]}
```
Regla: agrupar por texto de descripcion y severidad; `total` cuenta los warnings filtrados y `warnings_por_1000_elementos` usa todos los warnings del modelo. El bridge entrega la lista completa y `mcp-server` filtra, agrupa y trunca; el reporte siempre usa la lista completa.
Endpoint: `/warnings`.

## 6. audit_families

Proposito: inventario de riesgo de familias. La nomenclatura se audita en `audit_naming`.

Entrada: `{"checks": ["in_place", "unused", "duplicated", "type_count"], "type_count_threshold": 30}`.

Salida: sobre comun con `data: [{"check": "unused", "family": "", "category": "", "detail": "", "instances": 0}]` y `summary: {"in_place": 6, "unused": 41, "duplicated": 3, "type_count": 2}`.
Reglas: in-place permitidas por defecto 0; no usada = familia sin instancias colocadas; duplicada = nombre que difiere solo por sufijo de copia o numerico (`Copia`, `Copy`, `2`); exceso de tipos sobre el umbral.
Limitacion declarada: el tamano en disco de una familia no esta disponible en la API sin editarla; se usa el numero de tipos como indicador de peso.
Endpoint: `/families`.

## 7. audit_naming

Proposito: verificar la convencion de nombres del proyecto. Es la herramienta donde el modelo de lenguaje aporta lo que un script no: traduce la regla del BEP a una expresion regular.

Entrada:
```json
{"target": "views", "pattern": "^[A-Z]{2}-(PL|CO|EL)-\\d{3}$",
 "rule_text": "Vistas: disciplina, tipo y correlativo de tres digitos (BEP 4.2)",
 "category": null}
```
`target` admite `families`, `types`, `views`, `sheets`, `levels`.

Salida: `{"pattern_used": "", "rule_text": "", "checked": 320, "compliant": 287, "data": [{"name": "Planta 1 copia", "target": "views", "unique_id": ""}]}`.
Control: `mcp-server` compila el patron antes de llamar al bridge (`InvalidRegex` si falla) y el agente muestra el patron al usuario para confirmarlo antes de ejecutar.
Endpoint: `/names` con `args.target = "views"` (el bridge solo devuelve nombres; el regex se evalua en `mcp-server`).

## 8. audit_parameters

Proposito: completitud y validez de parametros exigidos por el cliente o el BEP.

Entrada:
```json
{"category": "Doors",
 "required": ["Mark", "Fire Rating"],
 "rules": [{"param": "Fire Rating", "allowed": ["EI30", "EI60", "EI90"]},
           {"param": "Mark", "regex": "^P-\\d{3}$"}]}
```

Salida: `{"checked": 210, "summary": [{"param": "Fire Rating", "missing": 0, "empty": 34, "invalid": 5}], "data": [{"unique_id": "", "param": "Fire Rating", "issue": "empty", "value": null}]}`.
Reglas: presente en el elemento o su tipo, no vacio, valor dentro de `allowed` o conforme a `regex`.
Endpoint: `/elements` con `fields` (reutiliza la extraccion de la herramienta 2; la evaluacion ocurre en `mcp-server`).

## 9. audit_links_coordinates

Proposito: diagnostico de vinculos y sistema de coordenadas. Solo diagnostico; la correccion queda fuera de la v1.

Entrada: `{"include_cad": true, "max_distance_from_origin": {"value": 10, "unit": "km"}}`.

Salida:
```json
{"base_point": {"ns": {"value": 0, "unit": "m"}, "ew": {"value": 0, "unit": "m"}, "elevation": {"value": 0, "unit": "m"}, "angle_to_true_north": {"value": 0, "unit": "deg"}},
 "survey_point": {"ns": {}, "ew": {}, "elevation": {}},
 "links": [{"name": "EST.rvt", "kind": "rvt", "loaded": true, "pinned": false, "positioning": "shared", "path_found": true}],
 "findings": [{"rule": "link_pinned", "target": "EST.rvt", "detail": "Vinculo sin fijar"}]}
```
Reglas: todo vinculo cargado y encontrado en su ruta; fijado; posicionado por coordenadas compartidas; CAD vinculado y no importado; punto base dentro de la distancia maxima al origen interno (Revit degrada la geometria lejos del origen).
Endpoint: `/links_coordinates`.

## 10. export_report

Proposito: entregar el resultado en el formato que pidieron los tres consultados. Corre completo en `mcp-server`; no llama al bridge.

Entrada: `{"sections": ["warnings", "families", "naming", "parameters", "links", "sheets_views"], "format": "xlsx", "path": null}`. Usa los resultados cacheados de la sesion.

Salida: `{"path": "C:/.../BIMAgent_Auditoria_<modelo>_<fecha>.xlsx", "sheets": ["Resumen", "Warnings", "..."], "health_score": {"value": 72, "max": 100, "components": [{"name": "warnings_por_1000", "value": 44, "weight": 0.25, "points": 15}]}}`.
Estructura del Excel: hoja `Resumen` (modelo, fecha, score y sus componentes, reglas aplicadas); una hoja por regla con columnas `Regla`, `Texto de la regla`, `UniqueId`, `ElementId`, `Elemento`, `Categoria`, `Nivel`, `Valor encontrado`, `Valor esperado`; hoja `Trazabilidad` con cada llamada (herramienta, argumentos, hora).
Score de salud: heuristica con pesos declarados en `config.py` (warnings por 1000 elementos, familias in-place, familias no usadas, vistas no colocadas, CAD importados, hallazgos de vinculos). Reemplaza a `audit_model_health` del Hito 1. Si faltan datos de algun componente, el score se calcula con los disponibles, se reparte el peso entre ellos y la salida lo declara con `complete: false` y `missing_components`. Las secciones sin datos en la sesion se devuelven en `sections_missing`; nunca se inventan.
