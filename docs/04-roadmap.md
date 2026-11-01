# Roadmap

Fechas oficiales: Hito 2 20/10/2026, Hito 3 12/11/2026. Detalle en `08-hito02-plan.md`, seccion 8.

## Fase 0 - Fundacion (cerrada 18/10)
- [x] Estructura de carpetas y CLAUDE.md
- [x] `02-contrato-herramientas.md` con las 10 tools
- [x] ADR-001 a ADR-005

## F1 - Vertical slice (1 y 2/11)
- [x] Bridge: `startup.py` + `/health` + `/overview` (falta prueba en Revit)
- [x] MCP: `revit_client.py` + `get_model_overview` (falta registro en Claude Desktop)
- Salida: Claude responde la radiografia leyendo un modelo real

## F2 - Flujo completo (3 y 4/11)
- [ ] `get_warnings`, `export_report` basico
- Salida: primer Excel real con UniqueId

## F3 - MVP indispensable (5 al 7/11)
- [ ] `get_sheets_and_views`, `audit_families`, `audit_naming`, `audit_parameters`, score
- Salida: herramientas 1, 4, 5, 6, 7, 8 y 10 operativas

## F4 - Alcance completo (8/11)
- [ ] `audit_links_coordinates`, `query_elements`, `get_quantities`
- Salida: las 10 herramientas, con reduccion declarada si hace falta

## F5 - Validacion (9 y 10/11)
- [ ] Panel pyRevit minimo, linea base cronometrada, prueba con usuarios, correcciones, video de respaldo
- Salida: CA-01 a CA-06 medidos

## F6 - Entrega (11 y 12/11)
- [ ] PPT final, ficha tecnica, instalacion por un tercero

MVP indispensable: herramientas 1, 4, 5, 6, 7, 8 y 10.
Reordenado el 2026-11-01: el flujo de extremo a extremo se cierra antes que la cobertura.
