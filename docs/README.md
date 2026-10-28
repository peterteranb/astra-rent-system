# Documentación

Versión final del 28/10/2026. Cómo instalar y correr el sistema está en el [README del proyecto](../README.md).

## Qué documento responde qué pregunta

| Pregunta | Dónde está la respuesta |
|---|---|
| ¿Quién usa el sistema y qué puede hacer cada uno? | [casos-de-uso.md](casos-de-uso.md#1-mapa): mapa de actores y la lista de los 16 casos de uso. |
| ¿Qué historias de usuario hay y cuándo se dan por cumplidas? | [casos-de-uso.md](casos-de-uso.md#4-historias-de-usuario): «Como… quiero… para…» con dado, cuando y entonces. |
| ¿Qué requisitos funcionales (RF) hay y cómo se verifica cada uno? | [casos-de-uso.md](casos-de-uso.md#2-requisitos-funcionales): dónde se cumple cada RF y qué prueba lo verifica. |
| ¿Qué requisitos de calidad (RC) hay y cómo se comprueban? | [casos-de-uso.md](casos-de-uso.md#3-requisitos-de-calidad). |
| ¿Qué pasa, paso a paso, en cada caso de uso? | [casos-de-uso.md](casos-de-uso.md#5-casos-de-uso): flujo normal, flujos alternativos con el mensaje exacto y el diagrama de secuencia con las funciones del código. |
| ¿Qué guarda cada botón en la base? | [casos-de-uso.md](casos-de-uso.md#6-qué-guarda-cada-botón). |
| ¿Qué quedó fuera de alcance y por qué? | [casos-de-uso.md](casos-de-uso.md#7-fuera-de-alcance). |
| ¿Qué tablas hay, por qué existe cada una y qué se calcula sin guardarse? | [base-de-datos.md](base-de-datos.md); el diagrama editable, en [base-de-datos.dbml](base-de-datos.dbml). |
| ¿Cómo está hecho el sistema: capas, carpetas, despliegue, log y correo? | [arquitectura.md](arquitectura.md). |
| ¿Qué endpoints JSON tiene el frontend, qué mandan y qué responden? | [api.md](api.md): cada endpoint con quién lo usa, ejemplos y errores, y cómo conectar React en desarrollo. |
| ¿Qué respondió el cliente? | [respuestas-del-cliente.md](respuestas-del-cliente.md): ENT-01 a ENT-98; desde ENT-66 separa lo que dijo el cliente de lo que completó el equipo. |
| ¿Qué decidió el equipo donde el cliente no respondió? | [decisiones.md](decisiones.md): D-01 a D-27, con su motivo y su ENT. |
| ¿Qué pruebas hay y cómo se corren? | [arquitectura.md](arquitectura.md#pruebas-y-ci) (tipos y CI), la sección «Pruebas» del [README del proyecto](../README.md#pruebas) (comando, cantidad y tiempo) y la columna «Cómo se verifica» de cada RF. |

## Cómo leer los IDs

| Prefijo | Qué es | Ejemplo | Dónde está |
|---|---|---|---|
| ENT-xx | Una respuesta del cliente; desde ENT-66, también lo que completó el equipo | ENT-73: hasta las 09:00 es a tiempo, hasta las 12:00 hay tolerancia y desde las 12:01 hay deuda | [respuestas-del-cliente.md](respuestas-del-cliente.md) |
| D-xx | Una decisión del equipo sin respuesta del cliente | D-06: las deudas por daño de una renta no pasan del valor del equipo | [decisiones.md](decisiones.md) |
| CU-xx | Un caso de uso | CU-04: rentar en línea y pagar con QR | [casos-de-uso.md](casos-de-uso.md) |
| HU-xx | Una historia de usuario | HU-09: registrar la devolución y cobrar el atraso | [casos-de-uso.md](casos-de-uso.md) |
| RF-xx | Un requisito funcional | RF-01: un equipo no se renta dos veces en las mismas fechas | [casos-de-uso.md](casos-de-uso.md) |
| RC-xx | Un requisito de calidad | RC-01: con 1000 equipos, el catálogo hace las mismas consultas | [casos-de-uso.md](casos-de-uso.md) |
| PRE-xx | Una necesidad del encargo original, anterior a las respuestas del cliente | PRE-03: registrar una renta | [presentacion12-10.md](presentacion12-10.md) |

Los documentos históricos usan IDs con otro formato (`PRE-RF-01`, `PRE-HU-01`, `PRE-CU-01`, `PB-01`). Se reemplazaron por los RF, HU y CU de [casos-de-uso.md](casos-de-uso.md), que dicen de qué ENT salen.

## Documentos históricos

Son de iteraciones anteriores. Se conservan como evidencia, con su fecha, y **no se actualizan**: si una regla cambió, vale la de los documentos de arriba.

| Documento | Qué tiene | Fecha |
|---|---|---|
| [sesion04.md](sesion04.md) | Primera iteración: backlog, alcance y ejemplos de aceptación del préstamo en memoria. | 01/10/2026 |
| [sesion-06-requisitos.md](sesion-06-requisitos.md) | Hallazgos de la primera entrevista y los primeros requisitos (`PRE-RF`). | 01/10/2026 |
| [sesion-07-modelos.md](sesion-07-modelos.md) | La primera historia, el caso de uso «el cliente renta un equipo» y su modelo. | 02/10/2026 |
| [sesion-08-09-plan.md](sesion-08-09-plan.md) | Plan del primer incremento: tareas, red, Gantt y disponibilidad. | 06/10/2026 |
| [presentacion12-10.md](presentacion12-10.md) | Avance presentado el 12/10: problema, alcance, necesidades PRE-01 a PRE-08 y cronograma. | 12/10/2026 |
| [diagramaGantt.png](diagramaGantt.png) | El Gantt de esa presentación. | 12/10/2026 |
| [sesion-12-arquitectura.md](sesion-12-arquitectura.md) | Arquitectura del primer flujo y su verificación con pruebas y CI. | 13/10/2026 |
| [sesion-13-14-revision.md](sesion-13-14-revision.md) | Revisión del estado del proyecto y correcciones prioritarias. | 14/10/2026 |
| [sesion-20-bocetos.md](sesion-20-bocetos.md) | Bocetos y recorridos del registro y el inicio de sesión. | 21/10/2026 |
