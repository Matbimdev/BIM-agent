# Roadmap

Entrega del MVP: 17/11/2026. Actualizado el 2026-11-11.

## F0 a F4 - Construccion (cerradas 01/11)
- [x] Estructura, contrato de las 10 herramientas y ADR-001 a ADR-006
- [x] Bridge pyRevit y servidor MCP registrado en Claude Desktop
- [x] Las 10 herramientas implementadas y probadas contra Revit 2026 con Snowdon
- [x] Excel con resumen, hoja por regla, trazabilidad y score
- [x] Correcciones de campo: categorias no modelo, ElementId en muestras, familias no usadas, `Element.Name`
- [x] Repositorio privado en GitHub

## F5 - Cierre tecnico (12 y 13/11)
- [ ] Contrastar el metrado de Floors con una tabla de planificacion de Revit (CA-04, diferencia menor a 0,5%)
- [ ] Contrastar 2 o 3 familias no usadas con `Select All Instances`
- [ ] Probar vinculos con un vinculo sin fijar y un CAD importado en una copia del modelo
- [ ] Panel pyRevit minimo: iniciar y detener el servidor, estado, seleccionar hallazgo por UniqueId
- [ ] Revisar pesos y limites del score en `config.py`
- [ ] Decidir el ruido de vistas no colocadas (tablas, 3D, planos de area) y de etiquetas sin uso

## F6 - Validacion (14 y 15/11)
- [ ] Linea base: auditoria manual cronometrada sobre Snowdon con las mismas reglas
- [ ] Prueba con 2 o 3 usuarios: tiempo, cobertura y comentarios
- [ ] Medir CA-01 a CA-06 y registrar errores y correcciones
- [ ] Video de demostracion continua de 3 a 5 minutos

## F7 - Entrega (16 y 17/11)
- [ ] Ficha tecnica: instalacion, dependencias, uso, datos de prueba, restricciones y reproduccion
- [ ] Instalacion por un tercero en otra maquina
- [ ] Quitar referencias academicas de `docs/02` y `docs/03`

MVP indispensable: herramientas 1, 4, 5, 6, 7, 8 y 10.
