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
- [x] Revit 2027 validado el 11/11: las 10 herramientas responden con Snowdon (1.450 elementos, metrado de Floors 6.513,544 m2, igual que en 2026; score 71). La falla anterior era de puerto: con Revit 2026 abierto primero, pyRevit asigna 48885 a 2027 y el MCP solo busca 48884
- [x] Robustez: si 48884 no responde o no tiene modelo, `revit_client.py` prueba `/health` en 48884 a 48890 y reintenta en el que tenga documento abierto (6 tests nuevos, 63 en total)
- [ ] Revisar por que 2027 da 56 vistas no colocadas y 2026 daba 55
- [x] CA-04 cumple. Metrado de Floors contrastado el 11/11 contra una tabla de
      planificacion de Revit 2027 (campos Type, Area y Count, sin filtro de fase,
      Itemize every instance desmarcado): 27 losas y 70.111,21 ft2 en los dos lados,
      con los cinco tipos coincidiendo uno a uno. Diferencia maxima 0,0005%, contra el
      0,5% que exige el criterio, y proviene de reconvertir a ft2 un valor que el MCP
      ya redondeo a tres decimales en m2. Evidencia en
      `samples/payloads/quantities_floors_snowdon.json`
- [ ] Contrastar 2 o 3 familias no usadas con `Select All Instances`
- [ ] Probar vinculos con un vinculo sin fijar y un CAD importado en una copia del modelo
- [x] Panel pyRevit minimo, probado en Revit 2027 el 11/11: `BIMAgent.tab/Auditoria.panel`
      con `Iniciar/Detener` (alterna el bridge), `Estado` (bridge, puerto, modelo y version)
      y `Seleccionar` (selecciona por UniqueId pegado desde el reporte). Pantalla P1 del
      Hito 2; cierra los pasos 1 y 9 del flujo de usuario y hace medible CA-03.
      Dos decisiones de implementacion: el panel no usa `pyrevit.forms`, que bajo CPython
      (Revit 2027) lanza `PyRevitCPythonNotSupported` en todos sus atributos, sino
      `TaskDialog` de la API de Revit; y `Estado` no llama a `/health` por HTTP, porque
      Routes despacha al hilo principal y el boton se bloquearia esperando su propia
      respuesta. 19 tests nuevos del parseo de UniqueId, 82 en total
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
