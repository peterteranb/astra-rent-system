# Iteración de la Sesión 04

## Equipo y proyecto
Gestión de préstamos de equipos — astra-rent-system
- Sofia Arduz Rengel
- Andres Laura Vargas
- Peter Uriel Teran Bedregal

## Backlog ordenado

| Orden | ID | Capacidad | ¿A quién ayuda y para qué? | Duda pendiente |
|---|---|---|---|---|
| 1 | PB-01 | Registrar un préstamo de un equipo disponible y rechazar otro préstamo si el equipo ya está activo | Operador — entrega equipos sin duplicar préstamos por error | Formato exacto del mensaje de rechazo (se dejó la decisión al equipo) |
| 2 | PB-02 | Registrar equipos individuales con identificador doble (número de serie + número de inventario interno), descripción y estado | Responsable del servicio — sin esto no hay qué prestar | Ninguna, ya acordada con el cliente |
| 3 | PB-03 | Consultar equipos y su disponibilidad con filtros relevantes | Operador / Responsable del servicio — saber qué hay libre antes de prestar | ¿Qué filtros son relevantes (estado, tipo de equipo)? — pendiente de preguntar |
| 4 | PB-04 | Registrar una devolución con fecha y observación sobre el estado del equipo | Operador — cierra el ciclo del préstamo y libera el equipo | ¿Una devolución con daño libera el equipo o lo bloquea? — pendiente |
| 5 | PB-05 | Identificar préstamos vencidos | Responsable del servicio — saber qué reclamar | ¿Cuál es la duración del préstamo? ¿Qué pasa exactamente al vencer? — pendiente |
| 6 | PB-06 | Permitir una corrección administrativa de un préstamo mal registrado, conservando motivo e historial | Operador — corrige errores sin perder trazabilidad | ¿Qué datos se pueden corregir y qué motivo se exige? — pendiente |

**Razón de la prioridad 1 (PB-01):** es la capacidad que el cliente pidió ver demostrada con pruebas para este avance, concentra la regla de negocio más incierta del proyecto (evitar el doble préstamo de un mismo equipo) y puede demostrarse en esta sesión usando datos de equipos y solicitantes fijos (fixtures), sin necesitar todavía una pantalla ni un flujo completo de alta de equipos.

## Objetivo y alcance

**Objetivo de la iteración:**
Al finalizar, el operador podrá registrar el préstamo de un equipo disponible a un solicitante, y el sistema rechazará un segundo préstamo del mismo equipo mientras el primero siga activo.

**Alcance de esta iteración:**
- Se implementa únicamente PB-01: registrar préstamo y rechazar préstamo duplicado.
- Los equipos y solicitantes se manejan como datos fijos/fixtures para las pruebas; no se implementa todavía el alta de equipos (PB-02) como capacidad propia, ni pantallas, ni base de datos.
- No se implementa un sistema de usuarios/autenticación; se simula un solicitante fijo, según lo autorizado por el cliente.
- El resto del backlog (PB-02 a PB-06) queda pendiente para próximas iteraciones.

## Aclaraciones del cliente

| Pregunta | Respuesta del cliente | Efecto sobre el comportamiento esperado |
|---|---|---|
| ¿Con qué identificamos un equipo, un código/ID único que asignamos nosotros, o un dato externo (n.º de serie, etiqueta física)? | Puede ser su número de serie, un número de inventario suyo, o ambos. El uso de ambos permite tener control con el proveedor y control interno. | Cada equipo deberá poder identificarse mediante su número de serie, su número de inventario interno o ambos. Queda pendiente definir si alguno será obligatorio y cómo se manejarán los casos en los que solo se disponga de uno. |
| Para esta versión, si un equipo está prestado y no volvió, ¿con eso ya alcanza para decir que no está disponible? ¿Mientras no vuelva, nadie más se lo puede llevar? | Sí. Le parece un buen inicio. | Un equipo con un préstamo activo se considerará no disponible y no podrá registrarse en otro préstamo hasta que se registre su devolución. |
| Cuando alguien pide un equipo que ya está prestado, ¿qué tan formal tiene que ser el rechazo? ¿Con un mensaje tipo "este equipo ya está prestado" alcanza, o se requiere algo más específico? | Es un prototipo. El cliente considera que en este punto el equipo debe mostrar sus estándares y metas; espera que el equipo de desarrollo proponga la solución. | El sistema deberá rechazar el préstamo de un equipo que ya esté prestado. El formato y nivel de detalle del mensaje de rechazo queda como decisión pendiente del equipo, que deberá proponerlo considerando los estándares y metas definidos para el prototipo. |
| Para el avance del lunes, si se pide no poner usuarios, pero el préstamo de equipos sí lo necesita, ¿se puede hacer la excepción? | Sí, pueden hacer la excepción, o pueden simular que existe un cliente. | Se simulará un solicitante fijo únicamente para poder registrar el préstamo; no se implementa un sistema de usuarios/autenticación en esta iteración. |
| ¿Qué debe mostrarse en el avance: solo los tests de las validaciones del préstamo de equipos? | Sí, solo se validan los tests de préstamo de equipos. Le parece bien porque muestra un norte claro del proyecto; quiere ver que el desarrollo tiene una idea clara. | La demostración de esta sesión se enfoca en la suite de pruebas de PB-01 (préstamo y rechazo), no en otras funcionalidades ni pantallas. |

## Ejemplos de aceptación

| Caso | Estado inicial y entrada | Resultado esperado | Regla que lo justifica |
|---|---|---|---|
| Uso normal | Equipo E1 (serie S001, inventario 001) disponible; solicitante Ana pide el préstamo | El préstamo se registra; E1 pasa a estado no disponible | Un equipo disponible puede prestarse (acordado con el cliente) |
| Límite | E1 acaba de ser prestado a Ana; inmediatamente después Juan intenta prestar el mismo E1 | El sistema rechaza el préstamo de Juan sin crear un segundo registro | Prestado = no disponible desde el momento del registro, sin ventana de tiempo (acordado con el cliente) |
| Rechazo / situación excepcional | E1 ya está prestado a Ana; Juan solicita E1 | Rechazo con un mensaje claro; no se crea un segundo préstamo activo para E1 | Un equipo con préstamo activo no puede volver a prestarse (acordado con el cliente) |

## Plan y seguimiento

| Tarea | Personas que colaboran | Estado | Evidencia o ubicación |
|---|---|---|---|
| Definir interfaz mínima (función `registrar_prestamo`, estructura de datos Equipo/Préstamo) | Los 3 en conjunto | Por hacer | `rent_manager/` |
| Escribir `test_acepta_prestamo_equipo_disponible` y `test_rechaza_prestamo_equipo_ya_prestado` | Pareja A | Por hacer | `tests/test_reglas.py` |
| Implementar la validación de disponibilidad en las reglas de negocio | Pareja A | Por hacer | `rent_manager/reglas.py` |
| Preparar datos ficticios de equipos y solicitante simulado (fixtures) | Persona C | Por hacer | `tests/` |
| Actualizar este documento (`docs/sesion04.md`) con resultados reales | Persona C | Por hacer | `docs/sesion04.md` |
| Revisión cruzada del PR e integración a `main` | Los 3 | Por hacer | PR en GitHub |

## Verificación e integración
Pendiente — completar con el resultado real de `python -m pytest -q`, el enlace del PR y el commit demostrado una vez integrado a `main`.

## Retroalimentación
Pendiente — completar durante la revisión con el cliente: petición o defecto identificado y el cambio correspondiente en el backlog.

## Retrospectiva
Pendiente — completar al cierre de la sesión: una práctica a mantener, una dificultad a cambiar, y un experimento concreto para la próxima iteración.

## Planificación y adaptación
Pendiente — completar con: qué decisión necesitó planificación previa, qué decisión mejoró gracias a una prueba o a la revisión del cliente, y en qué parte del proyecto convendría fijar más detalle por anticipado.
