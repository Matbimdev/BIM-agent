# Roadmap

Fechas oficiales: Hito 2 20/10/2026, Hito 3 12/11/2026. Detalle en `08-hito02-plan.md`, seccion 8.

## Fase 0 - Fundacion (cerrada 18/10)
- [x] Estructura de carpetas y CLAUDE.md
- [x] `02-contrato-herramientas.md` con las 10 tools
- [x] ADR-001 a ADR-005

## F1 - Vertical slice (19 al 23/10)
- [ ] Bridge: `startup.py` + `/health` + `/overview`
- [ ] MCP: `revit_client.py` + `get_model_overview` + registro en Claude Desktop
- Salida: Claude responde la radiografia leyendo un modelo real

## F2 - Nucleo de lectura (24 al 29/10)
- [ ] `query_elements`, `get_warnings`, `get_sheets_and_views`, fixtures y tests sin Revit
- Salida: CP-01, CP-02, CP-04, CP-05

## F3 - Auditoria (30/10 al 04/11)
- [ ] `audit_families`, `audit_naming`, `audit_parameters`, `audit_links_coordinates`, plantilla MCP
- Salida: CP-06 a CP-09

## F4 - Salida y metrado (05 al 07/11)
- [ ] `export_report` con score, `get_quantities`, panel pyRevit
- Salida: Excel generado, CP-03 dentro de 0,5%

## F5 - Validacion (08 al 10/11)
- [ ] Linea base cronometrada, prueba con usuarios, video de respaldo
- Salida: CA-01 a CA-06 medidos

## F6 - Entrega (11 y 12/11)
- [ ] PPT final, ficha tecnica, instalacion por un tercero

MVP indispensable: herramientas 1, 4, 5, 6, 7, 8 y 10.
