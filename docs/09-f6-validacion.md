# F6 - Validacion: linea base manual contra agente

Modelo: copia de Snowdon Towers Sample Structural en Revit 2026, con los 6 vinculos RVT de las
demas disciplinas y CAD de prueba (1.456 elementos antes de cargar los CAD). Es distinto del
Snowdon sin vinculos de CA-04 y CP-06, y se declara asi. Mismas reglas en los dos recorridos;
es la condicion de CA-01 y CA-02.

Archivo de F6: `PROYECTO/Snowdon Towers Sample Structural.rvt` (ignorado por git). CAD:
`Drawing1.dwg` importado y fijado, `ACI_01.dwg` vinculado sin fijar (personal, sin datos de
clientes; reemplaza a un DWG del trabajo que se retiro del modelo). Verificado el 14/11
al reabrir: `IsModified` falso, 1.458 elementos.

Tamano del modelo, para leer los tiempos manuales. Archivo de 26,5 MB, sin worksharing.
1.458 elementos de modelo: 942 Structural Framing, 91 Generic Models, 90 Structural Foundations,
76 Structural Beam Systems, 74 Structural Columns, 70 Structural Connections, 58 Walls, 27 Floors,
14 Structural Rebar, 7 Areas, 1 Shaft Opening, 6 vinculos RVT y 2 DWG. Ademas 1.287 elementos que
no son de modelo (bocetos, materiales, planos y similares). 185 familias cargadas, 19 niveles,
2 fases, 12 planos con 16 vistas colocadas y 55 vistas sin colocar, 2 warnings. Es un modelo
estructural chico o mediano: la revision manual se lleva casi todo su tiempo en familias
(185 en el navegador, 7:10) y vistas (71, 8:00), no en elementos.

Efecto conocido: `get_model_overview` cuenta `RVT Links` y cada DWG como elementos de modelo,
asi que el denominador de los warnings por mil sube (pendiente en F5 del roadmap).

## Antes de empezar

1. Cargar los CAD y guardar como copia de F6, cerrar y reabrir: asi el documento arranca sin
   cambios y CA-05 mide solo lo que hace el agente.
2. Cronometro por regla: se para al tener el hallazgo anotado, no al terminar de mirar.
3. No usar el agente ni el Excel durante la linea base, para no contaminar el recuento.
4. Al final, sin guardar: anotar si Revit marca el documento como modificado (CA-05).

## Reglas fijadas para F6

Los patrones de NOM y los parametros de PAR los fija el autor antes de cronometrar y no se
cambian despues. Snowdon no trae BEP: los patrones de NOM salen de la convencion dominante del
propio modelo (12 planos, 19 niveles), y se declara asi.

| Regla | Que se verifica | Metodo manual en Revit | Herramienta |
|-------|-----------------|------------------------|-------------|
| WRN | Warnings agrupados por descripcion | Gestionar > Advertencias, contar por texto | `get_warnings` |
| FAM-001 | Familias in-place | Seleccionar todo, Filtro, buscar categorias con familias in situ | `audit_families` |
| FAM-002 | Familias sin instancias colocadas | Navegador > Familias, `Seleccionar todas las instancias` por tipo; Purgar como apoyo | `audit_families` |
| FAM-003 | Duplicados por sufijo de copia o numerico | Revisar nombres en Navegador > Familias | `audit_families` |
| FAM-004 | Familias con mas de 30 tipos | Expandir familias en el navegador y contar tipos | `audit_families` |
| VIS-001 | Vistas exigibles sin plano | Navegador organizado por "No en planos", descartar 3D y planos de area | `get_sheets_and_views` |
| NOM-1 | Numero de plano `^S\d{3}$`: S y tres digitos | Lista de planos contra el patron | `audit_naming` sheet_numbers |
| NOM-2 | Nivel `^[LMR]\d( TOS)?$`: L, M o R, un digito, TOS opcional | Lista de niveles contra el patron | `audit_naming` levels |
| PAR-1 | Material estructural en Structural Framing | Tabla de planificacion con `Structural Material`, filtrar vacios | `audit_parameters` |
| VIN-001 | Vinculo cargado | Gestionar vinculos, columna Estado | `audit_links_coordinates` |
| VIN-002 | Vinculo encontrado en su ruta | Gestionar vinculos, columna Ruta | `audit_links_coordinates` |
| VIN-003 | Vinculo fijado | Seleccionar cada vinculo y ver el pin | `audit_links_coordinates` |
| VIN-004 | CAD importado y no vinculado | Gestionar vinculos > CAD, y Navegador > Importaciones | `audit_links_coordinates` |
| VIN-005 | CAD vinculado fijado | Seleccionar cada CAD y ver el pin | `audit_links_coordinates` |
| VIN-006 | Punto base a menos de 10 km del origen interno | Mostrar punto base y leer coordenadas | `audit_links_coordinates` |

## Registro

Manual: recorrido cronometrado por el autor el 14/11, regla por regla. WRN corregido de 02:12 a 00:25 por el autor (error al anotar).
Agente: 14/11, de 16:12:11 a 16:12:49, en Claude Code con las reglas ya fijadas. Nueve
llamadas (overview, warnings, familias, vistas, dos de nombres, parametros, vinculos y Excel),
casi todas en paralelo, asi que no hay tiempo por regla: se mide el bloque completo.

| Regla | Manual (mm:ss) | Hallazgos manual | Agente (mm:ss) | Hallazgos agente | Diferencia y por que |
|-------|----------------|------------------|----------------|------------------|----------------------|
| WRN | 00:25 | 2 | en bloque | 2: Insert conflicts with joined Wall; Floor thickness por Shape Editing | Igual |
| FAM-001 | 03:08 | 0 | en bloque | 0 | Igual |
| FAM-002 | 07:10 | 37 | en bloque | 44, lista en hoja Familias del Excel | Agente +7. Error de conteo manual: 185 familias en el navegador; sin lista manual por nombre |
| FAM-003 | 05:05 | 0 | en bloque | 0 | Igual |
| FAM-004 | 04:30 | 0 | en bloque | 0 (umbral 30 tipos) | Igual |
| VIS-001 | 08:00 | 35 | en bloque | 36 exigibles, lista en hoja Vistas no colocadas (mas 19 informativas: 12 3D y 7 planos de area) | Agente +1. Error de conteo manual; sin lista manual por nombre |
| NOM-1 | 04:00 | 0 | en bloque | 0 de 12 planos | Igual |
| NOM-2 | 02:15 | 7 | en bloque | 7 de 19: Elevator Pit, L1_35_Low, L1_37_Med, L1_43_High, Parapet 2, Parking, Top of Footing | Igual |
| PAR-1 | 04:45 | 0 | en bloque | 0 de 942 Structural Framing | Igual |
| VIN-001 | 02:34 | 0 | en bloque | 0 | Igual |
| VIN-002 | 02:11 | 0 | en bloque | 0 | Igual |
| VIN-003 | 03:05 | 6 | en bloque | 6: los 6 RVT de Snowdon sin fijar | Igual |
| VIN-004 | 02:07 | 1: Drawing1.dwg | en bloque | 1: Drawing1.dwg importado | Igual |
| VIN-005 | 03:00 | 1: ACI_01.dwg | en bloque | 1: ACI_01.dwg vinculado sin fijar | Igual |
| VIN-006 | 02:50 | 0 | en bloque | 0: punto base a 0 m del origen interno | Igual |
| Excel y score | no aplica | | en bloque | 9 hojas, score 59, completo | |
| Total | 55:05 | | 00:38 | | |

Excel: `Documents/BIMAgent/BIMAgent_Auditoria_Snowdon_Towers_20261114_161246.xlsx`.
Score 59 contra 76 del Snowdon limpio: los 8 hallazgos de vinculos le quitan los 15 puntos de
su componente y el DWG importado 1,5.

Los 38 s son ejecucion con las reglas ya escritas. No incluyen escribir los pedidos ni confirmar
los patrones de NOM, que en el uso real los hace la persona en el chat. El tiempo de un usuario
de punta a punta sale del video.

## Criterios

| Codigo | Criterio | Como se mide en F6 | Resultado |
|--------|----------|--------------------|-----------|
| CA-01 | Auditoria completa en menos de 5 minutos | Total del agente en la tabla de registro | Cumple: 38 s de ejecucion contra 55:05 manual. Falta el tiempo con usuario (video) |
| CA-02 | Cobertura igual o mayor que la manual | Reglas con resultado en cada columna; hallazgos que solo vio uno de los dos | Cumple en conteo: el agente iguala o supera al manual en las 15 reglas (FAM-002 44 contra 37, VIS-001 36 contra 35). Las 8 diferencias son errores de conteo manual declarados por el autor, sin cruce por nombre |
| CA-03 | Todo hallazgo tiene UniqueId y se selecciona en Revit | 20 hallazgos del Excel pegados en `Seleccionar` del panel | Cumple: 98 de 98 UniqueId del Excel se resuelven y 20 de 20 se seleccionan con el panel. Tras el arreglo del 14/11, el vinculo RVT se resalta y el panel ya no muestra el aviso |
| CA-04 | Metrado igual a la tabla de planificacion | Cumplido el 11/11, 0,0005% en Floors | Cumple |
| CA-05 | El modelo no se modifica | `Document.IsModified` falso al final de la sesion del agente | Cumple: falso al terminar, 14/11 16:13 |
| CA-06 | Ninguna respuesta oculta un truncado | Revisar cada respuesta: si `truncated` es verdadero, el chat lo dice | Cumple: las 9 respuestas con `truncated` falso |

## Observaciones

- IsModified volvio a verdadero despues de las 16:13 (CA-05 ya medido y cumplido a esa hora).
  La lista de Deshacer de Revit muestra dos operaciones de interfaz: "Modify Schedule/Quantities"
  y "Modify element attributes", de la prueba manual de CA-03 con tablas y vistas en Propiedades.
  No vienen del agente, que no abre transacciones.
- PAR-1 da 0 de 942. El Hito 2 (CP-08) esperaba 48 elementos estructurales sin material en
  Snowdon. Revisar de donde sale ese 48 antes de citarlo en el PPT.

## Errores y correcciones

| Fecha | Que fallo | Causa | Correccion |
|-------|-----------|-------|------------|
| 14/11 | Seleccionar mostraba "No good view could be found" con familias, vistas y tablas | `ShowElements` sobre elementos sin geometria en vista | El panel encuadra solo lo que no es familia, tipo o vista e informa cuantos se ven en Propiedades |
| 14/11 | VIN-003 apuntaba al RevitLinkType: el vinculo no se resaltaba | El bridge entregaba solo el UniqueId del tipo; la fijacion es de la instancia | Contrato, bridge y MCP: un hallazgo por instancia sin fijar con su UniqueId. Fixture `links_coordinates_snowdon.json`, 90 tests |

## CA-03: muestra de 20 hallazgos

Parte automatica, 14/11: las 98 filas de hallazgos del Excel (Warnings 3, Familias 44, Vistas
36, Vinculos 8, Nombres 2 7) tienen UniqueId valido, y los 98 se resuelven en el modelo con
`doc.GetElement`: 44 Family, 36 vistas (15 ViewPlan, 11 ViewSchedule, 10 ViewSection), 7 Level,
6 RevitLinkType, 2 ImportInstance, y un muro, un piso y una instancia en Warnings.

Parte manual: copiar cada grupo, pulsar `Seleccionar` en el panel y anotar que pasa en Revit.

| # | Hoja | Hallazgo | UniqueId | Panel |
|---|------|----------|----------|-------|
| 1 | Warnings | Opening, Generic Models, Parking | de2781c1-f964-4812-81d5-8f16b6a9ff61-000930f6 | Seleccionado y visible en 3D (GM_OpeningWall_Instance) |
| 2 | Warnings | Concrete 18", Walls, L1_43_High | 54d0215b-3923-47b8-beb3-55f8d5cea386-000e4b3a | Seleccionado y visible en 3D (Basic Wall Concrete 18") |
| 3 | Warnings | Concrete 12", Floors, L1_43_High | 54d0215b-3923-47b8-beb3-55f8d5cea386-000e4530 | Seleccionado y visible en 3D (Floor Concrete 12") |
| 4 | Familias | Anchor Tag | 03672b94-1f95-4663-8b80-dcfd5eabd061-000ea3f4 | Aviso de Revit No good view could be found; queda seleccionado en categoria Other, no se ve |
| 5 | Familias | Door-Opening | 03672b94-1f95-4663-8b80-dcfd5eabd061-000edbf9 | Aviso de Revit No good view could be found; queda seleccionado en categoria Other, no se ve |
| 6 | Familias | Hole Tag | 03672b94-1f95-4663-8b80-dcfd5eabd061-000f0ba7 | Aviso de Revit No good view could be found; queda seleccionado en categoria Other, no se ve |
| 7 | Familias | Fabric Sheet Tag | 03672b94-1f95-4663-8b80-dcfd5eabd061-000ef742 | Aviso de Revit No good view could be found; queda seleccionado en categoria Other, no se ve |
| 8 | Familias | Path Reinforcement Tag | 03672b94-1f95-4663-8b80-dcfd5eabd061-000f3faf | Aviso de Revit No good view could be found; queda seleccionado en categoria Other, no se ve |
| 9 | Vistas | East, Elevation | de2e16ba-d4a3-493e-aba1-7acb091c30a4-000314b3 | Aviso No good view could be found; queda seleccionada la vista East (Propiedades) |
| 10 | Vistas | L3, FloorPlan | a85b5f79-6bc1-4c71-bbd8-2d7187a3bf3f-0008dfb1 | Aviso No good view could be found; queda seleccionada la vista L3 (Propiedades) |
| 11 | Vistas | M1 TOS, FloorPlan | e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00097b9f | Aviso No good view could be found; queda seleccionada la vista M1 TOS |
| 12 | Vistas | Level Schedule | 63f8d234-f38c-4508-90c8-59b76e38f488-0008ec2a | Aviso No good view could be found; queda seleccionada la tabla Level Schedule |
| 13 | Vistas | View List | 24a97815-b3eb-45af-81b3-20434c195723-000e1d1d | Aviso No good view could be found; queda seleccionada la tabla View List |
| 14 | Vinculos | Snowdon Towers Sample Architectural.rvt | 9e748b35-2e51-4170-b964-a9c0f3c563d9-0008cbc7 | Aviso No good view could be found; queda seleccionado el vinculo (vinculos ocultos en la vista 3D) |
| 15 | Vinculos | Snowdon Towers Sample HVAC.rvt | 92788ff4-0a68-45a7-8a33-1830af59d54d-000c0248 | Aviso No good view could be found; queda seleccionado el vinculo (vinculos ocultos en la vista 3D) |
| 16 | Vinculos | Drawing1.dwg, importado | 50705696-d525-4a34-a4d7-fb81280be178-000fd390 | Seleccionado Drawing1.dwg |
| 17 | Vinculos | ACI_01.dwg, vinculado sin fijar | ce464692-68f7-441a-bb9f-f9cfc095bc64-000fd3ce | Seleccionado ACI_01.dwg |
| 18 | Nombres 2 | Elevator Pit | 9bb7de5c-5395-4e8d-83ae-c451a0c42cf3-000a6185 | Seleccionado el nivel Elevator Pit |
| 19 | Nombres 2 | L1_37_Med | e86e0fb0-aaef-4c8d-af36-9f1e0c4f7962-00096e54 | Seleccionado el nivel L1_37_Med |
| 20 | Nombres 2 | Parapet 2 | 63f8d234-f38c-4508-90c8-59b76e38f488-0008eff2 | Seleccionado el nivel Parapet 2 |

Resultado de la parte manual (14/11, vista 3D activa, vinculos ocultos en esa vista): 20 de 20
reportados, los 20 quedan seleccionados con el elemento correcto. Solo 8 se ven en el dibujo
(3 de warnings, 2 DWG, 3 niveles). En familias, vistas, tablas y vinculos RVT el panel muestra
el aviso de Revit "No good view could be found": `uidoc.ShowElements` no tiene donde encuadrar
un elemento sin geometria. Los UniqueId de vinculos RVT son del `RevitLinkType`, no de la
instancia colocada.

Repeticion tras el arreglo (14/11, pyRevit recargado, vinculos visibles en 3D): instancia del
vinculo Architectural, familia Anchor Tag y muro Concrete 18" pegados juntos. Sin aviso de Revit;
informe "Seleccionados: 3, 1 sin vista para encuadrar"; el filtro de seleccion muestra Other 1,
RVT Links 1 y Walls 1, y el vinculo se ve resaltado en la vista 3D.

## Casos de uso del autor

Dos tareas del trabajo real del autor, elegidas el 14/11, reproducidas sobre el mismo modelo.
Se fijan antes de cronometrar y no se cambian. Primero el recorrido manual, despues el agente.

A diferencia de la linea base, el agente se cronometra como lo usaria una persona: el autor
escribe la pregunta en Claude Code y para el cronometro cuando tiene la respuesta en pantalla.
Los dos recorridos se graban en pantalla, Revit y Claude Code lado a lado, como evidencia.
Ese tiempo incluye escribir el pedido, y responde a la salvedad de CA-01.

### CU-1. Metrado de concreto para presupuesto

Pregunta: "Volumen de concreto de cimentaciones por tipo y de muros por tipo y nivel, en m3."

- Manual: dos tablas de planificacion. Structural Foundations con Type, Count y Volume, sin
  itemizar. Walls con Type, Base Constraint y Volume, agrupada por tipo y nivel. Sin filtro de
  fase, como en CA-04. Anotar total y subtotales.
- Agente: `get_quantities` de Structural Foundations por tipo y de Walls por tipo y nivel.
- Criterio: diferencia menor a 0,5% por grupo (el mismo de CA-04).

### CU-2. Busqueda dirigida

Pregunta: "Que vigas del nivel L2 TOS tienen un Cut Length mayor a 18'."

Primera version descartada el 14/11: "vigas de L2 sin Mark". Ninguna viga de L2 tiene Mark, asi
que la respuesta era "todas" y no exigia filtrar. Se cambio antes de cronometrar al agente,
primero a 7' y luego a 18', por decision del autor. El nivel paso de L2 a L2 TOS, que es el
Reference Level de las vigas en Snowdon; con "L2" la herramienta compara exacto y daria 0.

- Manual: tabla de Structural Framing con Reference Level, Type y Cut Length, filtrada por L2 y
  Cut Length mayor que 18'. Anotar cuantas.
- Agente: `query_elements` de Structural Framing, nivel L2, filtro Cut Length gt. La herramienta
  compara en metros: el agente debe convertir 18' a 5,4864 m sin que se lo digan.
- Criterio: mismo conteo; el agente entrega UniqueId para `Seleccionar`. Una viga de 18' justos
  no entra en ninguno de los dos (mayor estricto).

| Caso | Manual (mm:ss) | Resultado manual | Agente (mm:ss) | Resultado agente | Diferencia |
|------|----------------|------------------|----------------|------------------|------------|
| CU-1 cimentaciones | 02:22 (las dos tablas) | 90 elementos, 361,62 m3: 24x24x20' 14 / 22,51; 24x24x25' 28 / 59,28; 30x30x25' 22 / 76,34; 36x36x24 Pile_24 12 / 6,12; 36x36x24 Pile_30 1 / 0,51; Bearing Footing - 36 9 / 56,88; FNDN-36 4 / 139,98 | 02:15 (las tres preguntas) | 90 elementos, 361,62 m3, 7 tipos. Igual al manual salvo 30x30x25': 76,35 contra 76,34 | 0,01 m3 (0,013%) por redondeo de la tabla a dos decimales. Cumple el 0,5% en los 7 grupos |
| CU-1 muros | incluido arriba | 58 muros, 1.164,94 m3. Elevator Pit 13 / 121,75 (10" 14,62; 12" 47,03; 18" 26,97; 24" 33,14). Top of Footing 18 / 404,81 (12" 30,81; 18" 40,72; 24" 333,28). L1_35_Low 5 / 77,74 (10" 45,69; 12" 32,04). L1_37_Med 5 / 72,96 (10" 56,79; 12" 16,17). L1_43_High 17 / 487,69 (12" 295,00; 18" 184,18; 24" 8,51) | incluido arriba | 58 muros, 1.164,94 m3, 4 tipos en 5 niveles. Mismos conteos por nivel. Igual al manual salvo Concrete 10" en L1_35_Low: 45,70 contra 45,69 | 0,01 m3 (0,02%) por redondeo. Cumple el 0,5% en los 14 grupos |
| CU-2 | 00:56 (grabacion 2:22 a 3:18) | 28 vigas con Reference Level L2 TOS: 17 16K6 de 22'-3" y 11 W18x55 entre 18'-8" y 27'-10" | incluido arriba | 28 vigas: 17 16K6 y 11 W18x55. Convirtio 18 ft a 5,486 m sin que se lo pidieran | Igual |

Agente: 14/11, sesion nueva de Claude Code con Opus 5.5 en esfuerzo medio, grabada junto a
Revit. 02:15 desde escribir la primera pregunta hasta la ultima respuesta, contra 03:18 a mano
(02:22 de CU-1 mas 00:56 de CU-2). El autor redacto las preguntas a su manera: CU-1 en dos
mensajes (cimentaciones y muros) y CU-2 como "total de vigas del nivel L2 TOS con Cut Length
mayor a 18 pies". El contenido es el del protocolo.

Lo que el agente agrego sin que se lo pidieran: separo las 17 viguetas 16K6 de los 11 perfiles W;
aviso que el metrado suma todas las fases; y marco que los dos tipos Pile dan unos 0,5 m3 por
unidad, posible senal de que el volumen cuenta solo el cabezal, y recomendo contrastarlo con la
tabla antes de presupuestar.
