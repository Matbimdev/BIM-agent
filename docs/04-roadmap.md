# Roadmap

Entrega del MVP: 17/11/2026. Actualizado el 2026-11-14.

## F0 a F4 - Construccion (cerradas 01/11)
- [x] Estructura, contrato de las 10 herramientas y ADR-001 a ADR-006
- [x] Bridge pyRevit y servidor MCP registrado en Claude Desktop
- [x] Las 10 herramientas implementadas y probadas contra Revit 2026 con Snowdon
- [x] Excel con resumen, hoja por regla, trazabilidad y score
- [x] Correcciones de campo: categorias no modelo, ElementId en muestras, familias no usadas, `Element.Name`
- [x] Repositorio privado en GitHub

## F5 - Cierre tecnico (cerrada 11/11)
- [x] Revit 2027 validado el 11/11: las 10 herramientas responden con Snowdon (1.450 elementos, metrado de Floors 6.513,544 m2, igual que en 2026; score 71). La falla anterior era de puerto: con Revit 2026 abierto primero, pyRevit asigna 48885 a 2027 y el MCP solo busca 48884
- [x] Robustez: si 48884 no responde o no tiene modelo, `revit_client.py` prueba `/health` en 48884 a 48890 y reintenta en el que tenga documento abierto (6 tests nuevos, 63 en total)
- [x] 56 vistas no colocadas en 2027 contra 55 en 2026: no es diferencia de version, es el
      modelo. `Legend 1` la creo el autor entre las dos corridas (confirmado el 11/11), y la
      tabla `Floor Schedule` del contraste de CA-04 sube la cuenta a 57. Son las dos vistas con
      ElementId mas alto del modelo. No guardar Snowdon con ellas (CA-05)
- [x] CA-04 cumple. Metrado de Floors contrastado el 11/11 contra una tabla de
      planificacion de Revit 2027 (campos Type, Area y Count, sin filtro de fase,
      Itemize every instance desmarcado): 27 losas y 70.111,21 ft2 en los dos lados,
      con los cinco tipos coincidiendo uno a uno. Diferencia maxima 0,0005%, contra el
      0,5% que exige el criterio, y proviene de reconvertir a ft2 un valor que el MCP
      ya redondeo a tres decimales en m2. Evidencia en
      `samples/payloads/quantities_floors_snowdon.json`
- [x] Familias no usadas contrastadas el 11/11 en Revit 2027. En simple: la regla FAM-002
      opina sobre 83 de las 185 familias del modelo; de esas, 44 estan sin usar y 39 en uso.
      Las demas reglas de familias (in-place, duplicadas, exceso de tipos) revisan las 185.
      Sobre las otras 102 (formas de armadura, perfiles, cabezas de nivel y similares, que
      se usan desde un tipo y no se colocan) no dice nada. De las 44 que reporta
      `audit_families`, 41 estan en categorias sin ningun elemento en el modelo y se
      deducen del propio overview; las 3 restantes (`SF_Reference Beam`, `SFD_Rectangle`,
      `EnscapeCamera`) se probaron a mano con `Select All Instances` tipo por tipo y con
      Purge Unused: cero instancias en las tres. `SF_Reference Beam` era la candidata a
      falso positivo por la limitacion declarada de familias usadas solo como referencia
      de tipo, y no se reprodujo.
      CP-06 queda mal redactado y se corrige: Purge Unused trabaja a nivel de tipo y
      lista familias en uso que tienen algun tipo sin usar, asi que las dos listas no
      pueden ser iguales. Lo demuestra `SF_Steel L Angle`, que aparece en Purge y tiene
      25 instancias del tipo `_Size`. Redaccion nueva: toda familia que la herramienta
      marca como no usada aparece en Purge; el recorrido inverso no aplica.
      Evidencia en `samples/payloads/familias_no_usadas_contraste.json`
- [x] CP-09 cumple, 11/11 en Revit 2026, sobre Snowdon con los 6 vinculos de las demas
      disciplinas y dos DWG de prueba personales: marca los 6 RVT sin fijar (confirmados a
      mano), marca el DWG importado aunque este fijado y no marca el DWG vinculado y fijado.
      La primera corrida fallo con `Name`: el bridge leia `RevitLinkType.Name`, que IronPython
      no resuelve; se corrigio con `serializers.element_name`. No se vio antes porque Snowdon
      sin vinculos nunca entraba en ese bucle. Sin probar: vinculo descargado o con ruta rota,
      CAD vinculado sin fijar y punto base lejos del origen. Evidencia en
      `samples/payloads/vinculos_contraste.json`
- [ ] `get_model_overview` cuenta `RVT Links` y cada DWG como categorias de modelo: con los
      vinculos, `elements_total` pasa de 1.450 a 1.457 y ese total es el denominador de los
      warnings por mil
- [x] Panel pyRevit minimo, probado en Revit 2027 el 11/11: `BIMAgent.tab/Auditoria.panel`
      con `Iniciar/Detener` (alterna el bridge), `Estado` (bridge, puerto, modelo y version)
      y `Seleccionar` (selecciona por UniqueId pegado desde el reporte). Pantalla P1 del
      Hito 2; cierra los pasos 1 y 9 del flujo de usuario y hace medible CA-03.
      Dos decisiones de implementacion: el panel no usa `pyrevit.forms`, que bajo CPython
      (Revit 2027) lanza `PyRevitCPythonNotSupported` en todos sus atributos, sino
      `TaskDialog` de la API de Revit; y `Estado` no llama a `/health` por HTTP, porque
      Routes despacha al hilo principal y el boton se bloquearia esperando su propia
      respuesta. 19 tests nuevos del parseo de UniqueId, 82 en total
- [x] Score revisado el 11/11 y declarado como heuristica provisional, sin recalibrar: con un
      solo modelo no hay con que calibrar. Snowdon limpio da 76; pierde 13,2 puntos por familias
      sin usar y 10,8 por vistas no colocadas. Limitacion declarada: familias y vistas son
      conteos absolutos y no escalan con el tamano del modelo. Pasar a proporciones queda para
      la v2
- [x] Ruido de vistas no colocadas, 11/11: cada vista lleva `required`. Son exigibles plantas,
      cortes, alzados, detalles, dibujos, leyendas y tablas; 3D y planos de area son
      informativas. Se devuelven todas, pero solo las exigibles van a la regla VIS-001 y al
      score. En Snowdon: 57 no colocadas, 38 exigibles y 19 informativas; el componente de
      vistas pasa de 0 a 3,6 de 15 puntos. Verificado contra Revit 2027. 5 tests nuevos, 87 en total
- [ ] Decidir el ruido de etiquetas sin uso: 24 de las 44 familias no usadas son etiquetas
      cargadas desde la plantilla

## F6 - Validacion (14 y 15/11)
- [x] Linea base, 14/11, sobre Snowdon 2026 con 6 vinculos RVT y dos DWG: 15 reglas, 55:05 a mano
      contra 38 s del agente. Mismos hallazgos en 13 reglas; en FAM-002 (44 contra 37) y VIS-001
      (36 contra 35) el manual conto de menos. Detalle en `docs/09-f6-validacion.md`
- [x] 2 casos de uso del autor, 14/11, grabados: metrado de concreto (CU-1) y vigas de L2 TOS
      con Cut Length mayor a 18' (CU-2). Mismos resultados que a mano, diferencias de 0,01 m3 por
      redondeo; 02:15 con el agente, escribiendo las preguntas, contra 03:18 a mano. Sin prueba
      con otros usuarios: el MCP no se comparte, y el sesgo de autor se declara como limitacion
- [x] CA-01 a CA-06 cumplen, 14/11. CA-03 encontro dos errores, corregidos: el aviso "No good
      view could be found" del panel y VIN-003 apuntando al tipo del vinculo. 90 tests
- [ ] Video de demostracion continua de 3 a 5 minutos

## F7 - Entrega (16 y 17/11)
- [ ] Ficha tecnica: instalacion, dependencias, uso, datos de prueba, restricciones y reproduccion
- [ ] Instalacion por un tercero en otra maquina (pendiente de decidir: o instalacion limpia en otro usuario de Windows)
- [ ] Quitar referencias academicas de `docs/02` y `docs/03`

MVP indispensable: herramientas 1, 4, 5, 6, 7, 8 y 10.
