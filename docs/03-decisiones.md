# Decisiones (ADR)

## ADR-001 - Bridge sobre pyRevit Routes
Fecha: 2026-09-01
Estado: aceptada

Contexto: se necesita exponer datos del Revit abierto a un proceso externo.
Opciones: pyRevit Routes, add-in C# con HttpListener, named pipes.

Decision: pyRevit Routes para todas las fases de validacion.

Razon: stack ya dominado, cero ciclo de compilacion, prototipo en horas.

Consecuencia: el cliente final necesita pyRevit instalado. Se mitiga manteniendo
el contrato JSON del bridge desacoplado, de modo que un add-in C# pueda reemplazarlo
sin tocar `mcp-server`.

Criterio de migracion a C#: primer cliente que no pueda instalar pyRevit, o
necesidad de escritura transaccional en el modelo.

## ADR-002 - Alcance de solo lectura
Fecha: 2026-09-01
Estado: aceptada

El agente lee, mide y audita. No modifica el modelo. Escribir desde un LLM en un
.rvt compartido es un riesgo que no se asume en la v1.

## ADR-003 - Limite de 10 herramientas
Fecha: 2026-09-01
Estado: aceptada

Mas tools degradan la seleccion del modelo. El presupuesto es fijo: agregar una
exige quitar otra y registrarlo aqui.

## ADR-004 - Granularidad agregada
Fecha: 2026-09-03
Estado: aceptada

Herramientas de nivel de flujo de trabajo, no metodos atomicos de la API. Diferenciacion
frente al servidor oficial de Revit 2027 (consulta generica) y frente a servidores de la
comunidad de 124 a 138 herramientas.

## ADR-005 - Lista revisada de 10 herramientas
Fecha: 2026-10-18
Estado: aceptada

Contexto: el feedback del Hito 1 pidio nombrar las diez herramientas con entrada, salida y
regla. La lista original no cubria tres capacidades elegidas por 2 de 3 consultados
(nomenclatura, parametros obligatorios, vinculos y coordenadas) y tenia un solapamiento
(`find_elements` con `get_element_parameters`).

Decision: se fusionan `get_project_info` en `get_model_overview` y `find_elements` con
`get_element_parameters` en `query_elements`. `audit_model_health` deja de ser herramienta y su
score se calcula en `export_report`. Entran `audit_naming`, `audit_parameters` y
`audit_links_coordinates`. El presupuesto se mantiene en 10.

Consecuencia: la informacion de proyecto ya no tiene herramienta propia pero viaja en la
radiografia inicial. El score de salud se vuelve configurable sin costo de seleccion para el modelo.

## ADR-006 - Token en el cuerpo JSON, endpoints POST

Fecha: 2026-10-18
Estado: aceptada

Contexto: el bridge escucha en localhost y cualquier proceso local podria consultar el modelo.
Lo estandar es enviar un token en la cabecera `Authorization`, pero pyRevit Routes de serie no
reenvia las cabeceras HTTP a las rutas. El laboratorio lo resolvio parcheando
`routes/server/server.py` de pyRevit, parche que se pierde al actualizar pyRevit.

Decision: todos los endpoints del bridge son POST y reciben `{"token": "...", "args": {...}}`.
El bridge genera el token al arrancar en `%APPDATA%\BIMAgent\token` si no existe; el
`mcp-server` lo lee del mismo archivo. Token invalido o ausente responde 401 con mensaje util.
La API se registra como `bim-agent` para convivir con otras extensiones en el mismo servidor Routes.

Consecuencia: funciona con pyRevit sin modificar y no depende del parche del laboratorio.
A cambio es menos estandar y hasta `/health` exige POST con token.
