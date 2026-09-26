# Iteración de la Sesión 04

## Equipo y proyecto
Gestión de préstamos de equipos — astra-rent-system

| Integrante | GitHub |
|---|---|
| Sofia Arduz Rengel | @arduz-in-zugzwang |
| Andres Laura Vargas | @andrewest-andrew |
| Peter Uriel Teran Bedregal | @peterteranb |

Cliente simulado: SergioCorp, empresa que renta equipos de amplificación para fiestas. El docente actúa como cliente.

Facilita y controla el tiempo: Andrew (también programa). En la programación en grupo una persona escribe, otra revisa la lógica y otra valida los ejemplos y los riesgos; rotamos cada ~10 minutos.
## Backlog ordenado

| Orden | ID | Capacidad | ¿A quién ayuda y para qué? | Duda pendiente |
|---|---|---|---|---|
| 1 | PB-01 | Registrar un préstamo de un equipo disponible y rechazar otro préstamo activo del mismo equipo | Operador — entrega equipos sin prestar dos veces la misma unidad | — (aclarada, ver abajo) |
| 2 | PB-02 | Registrar equipos individuales con número de inventario, número de serie, descripción y estado | Responsable del servicio — tener el inventario en el sistema y no en hojas de cálculo | ¿Qué estados puede tener un equipo? |
| 3 | PB-03 | Registrar solicitantes y verificar que existan antes de prestar | Operador — saber a quién se entrega cada equipo | ¿Cómo se identifica a una persona? |
| 4 | PB-04 | Consultar equipos y su disponibilidad con filtros relevantes | Operador y responsable — saber qué hay libre antes de comprometer un equipo | ¿Qué filtros son relevantes? |
| 5 | PB-05 | Registrar una devolución con fecha y observación sobre el estado del equipo | Operador — cerrar el préstamo y liberar el equipo | ¿Una devolución con daño libera el equipo o lo bloquea? |
| 6 | PB-06 | Diferenciar las acciones del operador de las consultas de otros usuarios | Responsable — que solo el personal registre préstamos | Mecanismo de identificación a acordar con el docente |

**Razón de la prioridad 1 (PB-01):** es la necesidad central del encargo ("evitar que un equipo se preste dos veces"); su regla ("disponible") era incierta y ya fue aclarada con el cliente; PB-04 y PB-05 necesitan préstamos registrados para existir; y se puede demostrar el lunes con una ejecución breve de las pruebas, usando datos ficticios en memoria en lugar de PB-02 y PB-03.

## Objetivo y alcance

> Al finalizar, el operador podrá registrar el préstamo de un equipo disponible a un solicitante y verá rechazado un segundo préstamo del mismo equipo, bajo las reglas acordadas de que cada equipo se identifica por su número de inventario y de que un préstamo activo basta para que no esté disponible.

**Pregunta de control:** sí, se demuestra ejecutando las pruebas, sin funcionalidades que todavía no existen.
 
**Alcance:**
- Se implementa solo PB-01. También se rechaza un equipo que no está en el inventario (decisión del equipo).
- Equipos y solicitantes son datos ficticios en memoria que prepara cada prueba. El solicitante se simula con su nombre, como autorizó el cliente.
- Fuera de alcance: alta de equipos y solicitantes, fechas y vencimientos, devoluciones, login, pantallas y base de datos.
- El resto del backlog queda pendiente y se actualizará después de la revisión.


## Aclaraciones del cliente

| Pregunta | Respuesta del cliente | Efecto sobre el comportamiento esperado |
|---|---|---|
| ¿Con qué identificamos un equipo, un código/ID único que asignamos nosotros, o un dato externo (n.º de serie, etiqueta física)? | "Puede ser su numero de serie / Un número de inventario suyo / Los dos / Para tener control con el proveedor e interno" | Cada equipo tiene número de inventario y número de serie. Decisión del equipo: el sistema usa el número de inventario para verificar la disponibilidad, así que dos equipos del mismo modelo son independientes. |
| Para esta versión, si un equipo está prestado y no volvió, ¿con eso ya alcanza para decir que no está disponible? | "Si. Supongo😎 / Me parece un buen inicio." | Un equipo con un préstamo activo no está disponible y se rechaza un nuevo préstamo. |
| Cuando alguien pide un equipo que ya está prestado, ¿qué tan formal tiene que ser el rechazo? | "Es un prototipo. / Creo q es ahí donde ustedes tienen q mostrarme. La idea es conocer sus estándares y metas." | Decisión del equipo: el rechazo lanza un error con un mensaje claro que nombra el equipo, y no se registra ningún préstamo. |
| Si no se agregan usuarios pero el préstamo necesita uno, ¿se puede hacer la excepción? | "Pueden hacer la excepción. O pueden simular q existe un cliente." | El solicitante se simula con su nombre; no hay login ni registro de usuarios. |
| ¿O solo necesita ver los tests de las validaciones? | "Si solo validan los test de préstamo de equipos" / "A mi me parece super bien porque muestra un norte a su proyecto. Pero quiero perspectiva. Q el proyecto al hacer esos tests se note q va para adelante y tiene una idea clara de desarrollo." | La demo muestra las pruebas de PB-01; el backlog muestra cómo sigue el proyecto. |

**Pendiente:** cómo se identifica a un solicitante; duración del préstamo; si una devolución con daño libera el equipo; mecanismo de login (mencionado en clase, a acordar en una iteración posterior).
## Ejemplos de aceptación

| Caso | Estado inicial y entrada | Resultado esperado | Regla que lo justifica |
|---|---|---|---|
| Uso normal | Inventario: INV-001 (parlante, serie S001), sin préstamos. Ana pide INV-001. | Se registra el préstamo INV-001 → Ana. INV-001 queda no disponible. | Un equipo sin préstamo activo puede prestarse (cliente). |
| Límite | Inventario: INV-001 e INV-002, dos parlantes del mismo modelo. INV-001 prestado a Ana. Juan pide INV-002. | Se acepta y se registra INV-002 → Juan. El préstamo de Ana no cambia. | La disponibilidad es por equipo (número de inventario), no por modelo (cliente). |
| Rechazo | INV-001 prestado a Ana. Juan pide INV-001. | Se rechaza con un mensaje que nombra INV-001. No se crea otro préstamo; el de Ana sigue igual. | Un préstamo activo deja el equipo no disponible (cliente); formato del rechazo decidido por el equipo. |
| Equipo inexistente (decisión del equipo) | El inventario no tiene INV-999. Juan pide INV-999. | Se rechaza con un mensaje que nombra INV-999. No se registra ningún préstamo. | Decisión del equipo: "no existe" y "ya prestado" son resultados distintos. |

## Plan y seguimiento

**Definition of Done:**
- [ ] Los ejemplos acordados tienen pruebas ejecutables que pasan.
- [ ] Las pruebas anteriores del proyecto continúan pasando.
- [ ] El código fue revisado por otro integrante.
- [ ] La contribución está integrada en `main` y fue comprobada allí.
- [ ] El README permite ejecutar las pruebas.
- [ ] El equipo puede demostrar el resultado y explicar sus límites.

**Interfaz mínima**:
 
```text
Equipment(inventory_id, serial_number, description)
Loan(inventory_id, borrower_name)
 
is_available(inventory, loans, inventory_id) -> bool
register_loan(inventory, loans, inventory_id, borrower_name) -> Loan
 
inventory: diccionario inventory_id -> Equipment
loans:     lista de Loan (todos activos en esta iteración)
errores:   EquipmentNotAvailableError, EquipmentNotFoundError
```
 
Cada prueba arma su propio inventario y su propia lista de préstamos.
 
| Tarea | Personas que colaboran | Estado | Evidencia o ubicación |
|---|---|---|---|
| T1. Estructura del repositorio, README y primer borrador de este documento | Sofía; revisaron Uriel y Andrew | Terminado | [PR #1](https://github.com/peterteranb/astra-rent-system/pull/1), [PR #2](https://github.com/peterteranb/astra-rent-system/pull/2) |
| T2. Confirmar la interfaz mínima y crear las funciones vacías | Uriel, Andrew, Sofía | En curso | `rent_manager/loans.py` |
| T3. Pruebas e implementación: uso normal y rechazo | Los 3, rotando | Por hacer | `tests/test_loans.py`, `rent_manager/loans.py` |
| T4. Pruebas e implementación: límite y equipo inexistente; refactorización | Los 3, rotando | Por hacer | `tests/test_loans.py`, `rent_manager/loans.py` |
| T5. PR, revisión, integración y verificación en `main` | Uriel abre, Andrew revisa, Sofía verifica en `main` | Por hacer | PR en GitHub |
 
Sesión de programación en grupo: sábado 26/09, 09:00. La rotación real y el punto de inspección se registran durante la sesión.

## Verificación e integración
Pendiente — resultado real de `python -m pytest -q`, enlace del PR y commit demostrado en `main`.

## Retroalimentación
Pendiente — petición o defecto identificado en la revisión y cambio correspondiente en el backlog.

## Retrospectiva
Pendiente — mantener, cambiar y experimentar.

## Planificación y adaptación
Pendiente — respuestas breves sobre las decisiones tomadas y su contexto.