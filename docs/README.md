# Documentación

Qué contiene: el índice de los documentos del sistema de renta de mesas y sillas de SergioCorp, el orden en que conviene leerlos y el glosario de IDs (ENT, D, CU, HU, RF, RC, PRE).
Cuándo leerlo: primero, antes que cualquier otro documento. Cómo instalar y correr el sistema está en el [README del proyecto](../README.md).

El sistema se usa sobre todo desde el frontend en React (`frontend/`), que no tiene reglas propias: llama a la API JSON ([api.md](api.md)), y la API llama a los mismos casos de uso que las páginas clásicas de Django.

## Índice

| Pregunta | Dónde está la respuesta |
|---|---|
| ¿Qué es un caso de uso, una historia, un requisito, y cómo se relacionan? | [casos-de-uso.md](casos-de-uso.md#cómo-se-relacionan-los-requisitos-las-historias-y-los-casos-de-uso) |
| ¿Quién usa el sistema y qué puede hacer cada uno? | [casos-de-uso.md](casos-de-uso.md#índice-por-actor): los 17 casos de uso agrupados por actor. |
| ¿Dónde está cada caso de uso en el código? | [casos-de-uso.md](casos-de-uso.md#dónde-está-cada-caso-de-uso): página, vista, función, reglas, tablas, log y prueba. |
| ¿Qué pasa, paso a paso, en cada caso de uso? | [casos-de-uso.md](casos-de-uso.md#cómo-leer-los-casos-de-uso): flujo normal, flujos alternativos con el mensaje exacto, el diagrama de secuencia y el de actividad. |
| ¿Qué requisitos funcionales (RF) y de calidad (RC) hay y cómo se verifica cada uno? | [casos-de-uso.md](casos-de-uso.md#requisitos-funcionales) y [requisitos de calidad](casos-de-uso.md#requisitos-de-calidad). |
| ¿Qué historias de usuario (HU) hay? | [casos-de-uso.md](casos-de-uso.md#historias-de-usuario). |
| ¿Cómo se cuentan los días de renta y el atraso? | [casos-de-uso.md](casos-de-uso.md#cómo-se-cuentan-los-días-y-el-atraso): las reglas y dos tablas de ejemplos con sus pruebas. |
| ¿Por qué estados pasan una renta, un equipo y una deuda? | [casos-de-uso.md](casos-de-uso.md#estados). |
| ¿Cómo está hecho el sistema: carpetas, capas, servidor, log, correo y CI? | [arquitectura.md](arquitectura.md). |
| ¿Qué tablas hay, qué guarda cada una y cómo se ve la base? | [base-de-datos.md](base-de-datos.md); el diagrama editable, en [base-de-datos.dbml](base-de-datos.dbml). |
| ¿Qué endpoints JSON usa el frontend en React? | [api.md](api.md). |
| ¿Qué respondió el cliente? | [respuestas-del-cliente.md](respuestas-del-cliente.md): [ENT-01](respuestas-del-cliente.md#ent-01) a [ENT-104](respuestas-del-cliente.md#ent-104). |
| ¿Qué decidió el equipo donde el cliente no respondió? | [decisiones.md](decisiones.md): [D-01](decisiones.md#d-01) a [D-42](decisiones.md#d-42). |
| ¿Qué pruebas hay, cómo se corren y cuánto cubren? | [pruebas.md](pruebas.md). |

## Orden de lectura recomendado

1. [README del proyecto](../README.md): qué es el sistema, cómo instalarlo y correrlo, y los usuarios de la demo.
2. Este documento, sobre todo el [glosario de IDs](#glosario-de-ids).
3. [casos-de-uso.md](casos-de-uso.md): empieza por «Cómo se relacionan…», el índice por actor y la tabla «Dónde está cada caso de uso»; después lee los casos de uso que te interesen.
4. [arquitectura.md](arquitectura.md): qué hay en cada carpeta y por qué.
5. [base-de-datos.md](base-de-datos.md): las tablas y cómo verlas en pgAdmin.
6. [pruebas.md](pruebas.md): cómo se comprueba todo.
7. Cuando un documento cite un ID, abre su enlace: [respuestas-del-cliente.md](respuestas-del-cliente.md) para las ENT y [decisiones.md](decisiones.md) para las D.
8. [api.md](api.md), solo si vas a trabajar en el frontend en React.

## Glosario de IDs

Cada ID es un enlace en los documentos: lleva a la fila donde se define.

| Prefijo | Qué es | Ejemplo | Dónde está |
|---|---|---|---|
| ENT-xx | Una respuesta del cliente (de una entrevista, por WhatsApp o al revisar el sistema). Desde [ENT-66](respuestas-del-cliente.md#ent-66) separa lo que dijo el cliente de lo que completó el equipo. | [ENT-73](respuestas-del-cliente.md#ent-73): hasta las 09:00 es a tiempo, hasta las 12:00 hay tolerancia sin cobro y desde las 12:01 hay deuda por atraso. | [respuestas-del-cliente.md](respuestas-del-cliente.md) |
| D-xx | Una decisión del equipo donde el cliente no dio una respuesta, con su motivo. | [D-06](decisiones.md#d-06): las deudas por daño de una renta nunca suman más que el valor del equipo. | [decisiones.md](decisiones.md) |
| CU-xx | Un caso de uso: los pasos de una persona con el sistema para lograr algo. | [CU-04](casos-de-uso.md#cu-04): rentar en línea y pagar con QR simulado. | [casos-de-uso.md](casos-de-uso.md#índice-por-actor) |
| HU-xx | Una historia de usuario: «Como…, quiero… para…», con su ejemplo «dado, cuando, entonces». | [HU-09](casos-de-uso.md#hu-09): registrar la devolución y cobrar el atraso. | [casos-de-uso.md](casos-de-uso.md#historias-de-usuario) |
| RF-xx | Un requisito funcional: una regla que el sistema cumple y que se puede probar. | [RF-01](casos-de-uso.md#rf-01): un equipo no se renta dos veces en las mismas fechas. | [casos-de-uso.md](casos-de-uso.md#requisitos-funcionales) |
| RC-xx | Un requisito de calidad: qué tan bien lo hace, con una medida. | [RC-01](casos-de-uso.md#rc-01): con 1000 equipos, el catálogo hace las mismas consultas que con 20. | [casos-de-uso.md](casos-de-uso.md#requisitos-de-calidad) |
| PRE-xx | Una necesidad del encargo original, anterior a las respuestas del cliente. | [PRE-03](presentacion12-10.md): registrar una renta. | [presentacion12-10.md](presentacion12-10.md) |

## Entregas anteriores

Son de iteraciones anteriores del curso. Se conservan como evidencia y **no se actualizan**: si una regla cambió, vale la de los documentos de arriba. Usan IDs con otro formato (`PRE-RF-01`, `PRE-HU-01`, `PRE-CU-01`, `PB-01`), que se reemplazaron por los RF, HU y CU de [casos-de-uso.md](casos-de-uso.md).

| Documento | Qué tiene | Fecha |
|---|---|---|
| [sesion04.md](sesion04.md) | Primera iteración: backlog, alcance y ejemplos de aceptación del préstamo en memoria. | 01/10/2026 |
| [sesion-06-requisitos.md](sesion-06-requisitos.md) | Hallazgos de la primera entrevista y los primeros requisitos (`PRE-RF`). | 01/10/2026 |
| [sesion-07-modelos.md](sesion-07-modelos.md) | La primera historia, el caso de uso «el cliente renta un equipo» y su modelo. | 02/10/2026 |
| [sesion-08-09-plan.md](sesion-08-09-plan.md) | Plan del primer incremento: tareas, red, Gantt y disponibilidad. | 06/10/2026 |
| [presentacion12-10.md](presentacion12-10.md) | Avance presentado el 12/10: problema, alcance, necesidades [PRE-01](presentacion12-10.md) a [PRE-08](presentacion12-10.md) y cronograma. | 12/10/2026 |
| [diagramaGantt.png](diagramaGantt.png) | El Gantt de esa presentación. | 12/10/2026 |
| [sesion-12-arquitectura.md](sesion-12-arquitectura.md) | Arquitectura del primer flujo y su verificación con pruebas y CI. | 13/10/2026 |
| [sesion-13-14-revision.md](sesion-13-14-revision.md) | Revisión del estado del proyecto y correcciones prioritarias. | 14/10/2026 |
| [sesion-20-bocetos.md](sesion-20-bocetos.md) | Bocetos y recorridos del registro y el inicio de sesión. | 21/10/2026 |
