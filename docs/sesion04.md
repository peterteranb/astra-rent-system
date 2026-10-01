# Iteración de la Sesión 04

## Equipo y proyecto
Gestión de préstamos de equipos — astra-rent-system

| Integrante                 | GitHub             |
|----------------------------|--------------------|
| Sofia Arduz Rengel         | @arduz-in-zugzwang |
| Andres Laura Vargas        | @andrewest-andrew  |
| Peter Uriel Teran Bedregal | @peterteranb       |

Cliente simulado: SergioCorp, empresa que renta equipos de amplificación para fiestas. El docente actúa como cliente.

Facilita y controla el tiempo: Andrew (también programa). En la programación en grupo una persona escribe, otra revisa la lógica y otra valida los ejemplos y los riesgos; rotamos cada ~10 minutos.

## Backlog ordenado

| Orden | ID    | Capacidad                                                                                      | ¿A quién ayuda y para qué?                                                            | Duda pendiente                                          |
|-------|-------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------|
| 1     | PB-01 | Registrar un préstamo de un equipo disponible y rechazar otro préstamo activo del mismo equipo | Operador — entrega equipos sin prestar dos veces la misma unidad                      | — (aclarada, ver abajo)                                 |
| 2     | PB-02 | Registrar equipos individuales con número de inventario, número de serie, descripción y estado | Responsable del servicio — tener el inventario en el sistema y no en hojas de cálculo | ¿Qué estados puede tener un equipo?                     |
| 3     | PB-03 | Registrar solicitantes y verificar que existan antes de prestar                                | Operador — saber a quién se entrega cada equipo                                       | ¿Cómo se identifica a una persona?                      |
| 4     | PB-04 | Consultar equipos y su disponibilidad con filtros relevantes                                   | Operador y responsable — saber qué hay libre antes de comprometer un equipo           | ¿Qué filtros son relevantes?                            |
| 5     | PB-05 | Registrar una devolución con fecha y observación sobre el estado del equipo                    | Operador — cerrar el préstamo y liberar el equipo                                     | ¿Una devolución con daño libera el equipo o lo bloquea? |
| 6     | PB-06 | Diferenciar las acciones del operador de las consultas de otros usuarios                       | Responsable — que solo el personal registre préstamos                                 | Mecanismo de identificación a acordar con el docente    |

**Razón de la prioridad 1 (PB-01):** es la necesidad central del encargo ("evitar que un equipo se preste dos veces"); su regla ("disponible") era incierta y ya fue aclarada con el cliente; PB-04 y PB-05 necesitan préstamos registrados para existir; y se puede demostrar el Lunes 28/09/2026 con una ejecución breve de las pruebas, usando datos ficticios en memoria en lugar de PB-02 y PB-03.

## Objetivo y alcance

> Al finalizar, el operador podrá registrar el préstamo de un equipo disponible a un solicitante y verá rechazado un segundo préstamo del mismo equipo, bajo las reglas acordadas de que cada equipo se identifica por su número de inventario y de que un préstamo activo basta para que no esté disponible.

**Pregunta de control:** sí, se demuestra ejecutando las pruebas, sin funcionalidades que todavía no existen.
 
**Alcance:**
- Se implementa solo PB-01. También se rechaza un equipo que no está en el inventario (decisión del equipo).
- Equipos y solicitantes son datos ficticios en memoria que prepara cada prueba. El solicitante se simula con su nombre, como autorizó el cliente.
- Fuera de alcance: alta de equipos y solicitantes, fechas y vencimientos, devoluciones, login, pantallas y base de datos.
- El resto del backlog queda pendiente y se actualizará después de la revisión.


## Aclaraciones del cliente

| Pregunta                                                                                                                        | Respuesta del cliente                                                                                                                                                                                                                              | Efecto sobre el comportamiento esperado                                                                                                                                                                          |
|---------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ¿Con qué identificamos un equipo, un código/ID único que asignamos nosotros, o un dato externo (n.º de serie, etiqueta física)? | "Puede ser su numero de serie / Un número de inventario suyo / Los dos / Para tener control con el proveedor e interno"                                                                                                                            | Cada equipo tiene número de inventario y número de serie. Decisión del equipo: el sistema usa el número de inventario para verificar la disponibilidad, así que dos equipos del mismo modelo son independientes. |
| Para esta versión, si un equipo está prestado y no volvió, ¿con eso ya alcanza para decir que no está disponible?               | "Si. Supongo😎 / Me parece un buen inicio."                                                                                                                                                                                                        | Un equipo con un préstamo activo no está disponible y se rechaza un nuevo préstamo.                                                                                                                              |
| Cuando alguien pide un equipo que ya está prestado, ¿qué tan formal tiene que ser el rechazo?                                   | "Es un prototipo. / Creo q es ahí donde ustedes tienen q mostrarme. La idea es conocer sus estándares y metas."                                                                                                                                    | Decisión del equipo: el rechazo lanza un error con un mensaje claro que nombra el equipo, y no se registra ningún préstamo.                                                                                      |
| Si no se agregan usuarios pero el préstamo necesita uno, ¿se puede hacer la excepción?                                          | "Pueden hacer la excepción. O pueden simular q existe un cliente."                                                                                                                                                                                 | El solicitante se simula con su nombre; no hay login ni registro de usuarios.                                                                                                                                    |
| ¿O solo necesita ver los tests de las validaciones?                                                                             | "Si solo validan los test de préstamo de equipos" / "A mi me parece super bien porque muestra un norte a su proyecto. Pero quiero perspectiva. Q el proyecto al hacer esos tests se note q va para adelante y tiene una idea clara de desarrollo." | La demo muestra las pruebas de PB-01; el backlog muestra cómo sigue el proyecto.                                                                                                                                 |

**Pendiente:** cómo se identifica a un solicitante; duración del préstamo; si una devolución con daño libera el equipo; mecanismo de login (mencionado en clase, a acordar en una iteración posterior).

Preguntas surgidas durante el desarrollo (quedan como pruebas marcadas con `skip` en `tests/`):
- ¿Qué nombres de solicitante son válidos (vacíos, con espacios, con caracteres especiales)?
- ¿El número de inventario distingue mayúsculas y minúsculas (`inv-001` frente a `INV-001`)?
- ¿Hay un límite de equipos por persona?
- ¿Se puede modificar un préstamo ya registrado? El P01 pide conservar el historial.

## Ejemplos de aceptación

| Caso                                     | Estado inicial y entrada                                                                                  | Resultado esperado                                                                             | Regla que lo justifica                                                                                 |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Uso normal                               | Inventario: INV-001 (parlante, serie S001), sin préstamos. Ana pide INV-001.                              | Se registra el préstamo INV-001 → Ana. INV-001 queda no disponible.                            | Un equipo sin préstamo activo puede prestarse (cliente).                                               |
| Límite                                   | Inventario: INV-001 e INV-002, dos parlantes del mismo modelo. INV-001 prestado a Ana. Juan pide INV-002. | Se acepta y se registra INV-002 → Juan. El préstamo de Ana no cambia.                          | La disponibilidad es por equipo (número de inventario), no por modelo (cliente).                       |
| Rechazo                                  | INV-001 prestado a Ana. Juan pide INV-001.                                                                | Se rechaza con un mensaje que nombra INV-001. No se crea otro préstamo; el de Ana sigue igual. | Un préstamo activo deja el equipo no disponible (cliente); formato del rechazo decidido por el equipo. |
| Equipo inexistente (decisión del equipo) | El inventario no tiene INV-999. Juan pide INV-999.                                                        | Se rechaza con un mensaje que nombra INV-999. No se registra ningún préstamo.                  | Decisión del equipo: "no existe" y "ya prestado" son resultados distintos.                             |

## Plan y seguimiento

**Definition of Done:**
- [x] Los ejemplos acordados tienen pruebas ejecutables que pasan.
- [x] Las pruebas anteriores del proyecto continúan pasando.
- [x] El código fue revisado por otro integrante.
- [x] La contribución está integrada en `main` y fue comprobada allí.
- [x] El README permite ejecutar las pruebas.
- [x] El equipo puede demostrar el resultado y explicar sus límites (demostrado el lunes 28/09/2026).

**Interfaz mínima** (aceptada por los tres antes de programar):

```text
Equipment(inventory_id, serial_number, description)
Loan(inventory_id, borrower_name)

is_available(inventory, loans, inventory_id) -> bool
register_loan(inventory, loans, inventory_id, borrower_name) -> Loan

inventory: diccionario inventory_id -> Equipment
loans:     lista de Loan (todos activos en esta iteración)
errores:   EquipmentNotAvailableError, EquipmentNotFoundError
```

Cada prueba arma su propio inventario y su propia lista de préstamos. `is_available` devuelve `False` si el equipo no está registrado; `register_loan` distingue los dos rechazos con su error.

| Tarea                                                                         | Personas que colaboran                              | Estado      | Evidencia o ubicación                                                                                                                                                                               |
|-------------------------------------------------------------------------------|-----------------------------------------------------|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| T1. Estructura del repositorio, README y primer borrador de este documento    | Sofia; revisaron Uriel y Andrew                     | Terminado   | [PR #1](https://github.com/peterteranb/astra-rent-system/pull/1), [PR #2](https://github.com/peterteranb/astra-rent-system/pull/2), [PR #3](https://github.com/peterteranb/astra-rent-system/pull/3)                                                                  |
| T2. Interfaz mínima e implementación inicial                                  | Uriel escribe; Sofía y Andrew acompañan             | Terminado   | `rent_manager/loans.py`, [PR #5](https://github.com/peterteranb/astra-rent-system/pull/5) |
| T3. Pruebas de `is_available` y `register_loan`; datos propios en cada prueba | Sofia escribe; Uriel y Andrew acompañan             | Terminado   | `tests/test_loans.py`, [PR #5](https://github.com/peterteranb/astra-rent-system/pull/5) |
| T4. Casos borde, errores de dominio y pruebas de los 4 ejemplos acordados     | Andrew y Uriel escriben; se revisan entre los tres  | Terminado   | `tests/test_loans_edge_cases.py`, `tests/test_loans.py`, `rent_manager/loans.py`, [PR #5](https://github.com/peterteranb/astra-rent-system/pull/5) |
| T5. PR, revisión, integración y verificación en `main`                        | Uriel abre, Sofía revisa, Andrew verifica en `main` | Terminado   | [PR #5](https://github.com/peterteranb/astra-rent-system/pull/5)                                                                                                                                    |

**Sesión de programación en grupo:** sábado 26/09, de 11:00 a 12:00. Andrew facilitó y controló el tiempo. Una persona escribía por turno y las otras acompañaban.

| Bloque | Trabajo                                         | Escribió                             | Aporte de quienes acompañaron                                                                                           |
|--------|-------------------------------------------------|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| 1      | Interfaz e implementación inicial de `loans.py` | Uriel                                | Sofía ayudó con la sintaxis de las funciones; Andrew cuestionó cómo informar el rechazo (mensaje, `print` o error).     |
| 2      | Pruebas de `is_available` y `register_loan`     | Sofía                                | Uriel y Andrew corrigieron la sintaxis y quitaron el inventario fijo de `loans.py` para que cada prueba arme sus datos. |
| 3      | Casos borde y preguntas pendientes              | Andrew (en parte de forma asíncrona) | Uriel corrigió la marca `skip`; Sofía revisó qué comprobaba cada prueba.                                                |

Después de la sesión, de forma asíncrona: Uriel propuso y aplicó el cambio de rechazos en texto a los errores acordados (primero las pruebas, luego la implementación) y escribió las pruebas de los 4 ejemplos; Andrew agregó la prueba de que registrar un préstamo no modifica el inventario.

**Punto de inspección (sábado, durante la sesión):**
1. Comprobado: la estructura y pruebas que verifican las funciones.
2. Faltaba: completar T3 y T4, verificar el README y T5.
3. Obstáculo: cómo ejecutar las pruebas con sus propios datos, sin el inventario fijo en `loans.py`.
4. Siguientes veinte minutos: implementar T3 y T4.

Ajuste del plan: se quitaron los datos fijos de `loans.py` y cada prueba prepara su estado. Luego se detectó que los rechazos devolvían texto en lugar de los errores acordados, y se corrigió siguiendo la interfaz.

## Verificación e integración

| Ejemplo            | Prueba                                          |
|--------------------|-------------------------------------------------|
| Uso normal         | `test_example_normal_loan_of_available_unit`    |
| Límite             | `test_example_boundary_two_units_of_same_model` |
| Rechazo            | `test_example_rejection_unit_already_on_loan`   |
| Equipo inexistente | `test_example_unregistered_unit`                |

- Comando: `python -m pytest -v`
- Resultado en la rama `iteracion01/register-loan`: 21 pasan y 4 se omiten (`skip`), en las computadoras de los tres (Windows y Linux). Las 4 omitidas corresponden a decisiones pendientes del cliente y a devoluciones (PB-05).
- PR: [PR #5](https://github.com/peterteranb/astra-rent-system/pull/5) (el PR #4 se abrió por error y se cerró sin integrar).
- Revisión: Sofía, segunda lectura (participó en la solución, no es una revisión independiente).
- Commit demostrado en `main`: `cb84e69`.
- Resultado en `main`: 21 pasan y 4 se omiten (`skip`).
  - Windows (Python 3.14.6, pytest 9.1.1): `21 passed, 4 skipped in 0.28s`.
  - Linux (Andrew): mismo resultado, 21 pasan y 4 se omiten.
- Demostración: lunes 28/09/2026, ejecutando la suite sobre `main` (commit `cb84e69`).

## Retroalimentación
**Revisión del lunes 28/09/2026.** Sergio revisó las pruebas de PB-01 y pidió que explicáramos su funcionamiento; cada integrante respondió y defendió el comportamiento acordado.

- **Petición nueva:** ninguna. No pidió agregar, cambiar ni quitar funcionalidades.
- **Defecto:** ninguno. La revisión no mostró que incumpliéramos una regla ya acordada, así que no se registra ningún defecto pendiente.
- **Cambio en el backlog:** ninguno por ahora. Los seis elementos (PB-01 a PB-06) y su orden se mantienen; PB-01 queda terminado. El orden de la siguiente iteración se decide con el cliente y todavía no está acordado.

Lo que sí quedó claro es que el cliente espera que el proyecto muestre "perspectiva": que las pruebas de hoy se noten como un paso de un desarrollo con dirección. Por eso las preguntas pendientes de las secciones anteriores (estados del equipo, identificación del solicitante, duración del préstamo, devolución con daño, login) siguen registradas como pendientes y no como reglas asumidas.

## Retrospectiva
**Mantener:** escribir primero la prueba y corregir después. Cuando notamos que los rechazos devolvían un texto en vez de las excepciones acordadas (`EquipmentNotAvailableError` / `EquipmentNotFoundError`), Uriel corrigió primero las pruebas y luego la implementación; se comprobó porque esas pruebas fallaban antes del cambio y pasaron después, sin romper los demás casos.

**Cambiar:** empezamos con datos de inventario fijos dentro de `loans.py`, y a mitad de la sesión nos dimos cuenta de que eso acoplaba las pruebas entre sí. Tuvimos que parar, quitar los datos fijos y rehacer que cada prueba armara su propio inventario y su propia lista de préstamos, lo que nos quitó tiempo que teníamos planeado para T4.

**Experimentar:** antes de la próxima sesión de grupo, dejar por escrito qué prepara cada prueba por sí misma (igual que ya acordamos la interfaz mínima), en vez de decidirlo sobre la marcha. Lo impulsa Andrew, que facilita la sesión. Lo comprobamos si en el próximo punto de inspección de cinco minutos no aparece ningún ajuste del tipo "quitar datos compartidos".

## Planificación y adaptación
**¿Qué decisión necesitaba planificación antes de programar?**  Qué datos tendría cada equipo (número de inventario, número de serie, descripción) y qué resultado/mensaje debía producir un préstamo según si el equipo estaba disponible o no. Por eso acordamos la interfaz mínima (`Equipment`, `Loan`, `is_available`, `register_loan` y los dos errores) antes de programar; sin ese acuerdo, quien escribía las pruebas podría haber usado una interfaz distinta de la implementada.

**¿Qué decisión pudieron mejorar gracias a una prueba o a la revisión del cliente?**   
*Gracias a una prueba:* al escribir los cuatro ejemplos de aceptación notamos que el rechazo devolvía un texto simple en vez de una excepción, así que lo cambiamos a `EquipmentNotAvailableError` / `EquipmentNotFoundError`, que es más fácil de comprobar y distingue los dos motivos de rechazo.  
*Gracias a la revisión del cliente:* ninguna decisión cambió. En la revisión del lunes el cliente revisó las pruebas y no pidió cambios ni señaló defectos. Las aclaraciones que influyeron en el código (cómo identificar un equipo, qué tan formal es el rechazo) se dieron antes de programar, no como resultado de revisar el código ya hecho.  

**¿En qué contexto de su proyecto sería útil fijar más detalles por anticipado?**  
En `is_available` y `register_loan`, `inventory_id` se compara como texto exacto (inventory_id not in inventory) y `borrower_name` se guarda tal cual, sin normalizar. Eso ya es una decisión implícita: ahora mismo INV-001 e inv-001 son equipos distintos para el sistema, y un nombre con espacios o caracteres raros se acepta sin validar. Como no confirmamos con el cliente si el número de inventario distingue mayúsculas o qué nombres de solicitante son válidos, dejamos esas pruebas con skip en vez de asumir una regla. Si hubiéramos fijado eso antes de escribir `is_available`, no tendríamos ese código implementado con un comportamiento que quizás haya que cambiar después.

**¿Qué costo tendría hacerlo si las reglas todavía cambian?** Si fijamos ahora una regla que el cliente todavía no confirmó (por ejemplo, cuántos días dura un préstamo o si una devolución con daño libera el equipo), y su respuesta real termina siendo distinta, tendríamos que reescribir el código y las pruebas que ya hicimos para esa regla, y en una iteración con base de datos también los datos ya guardados. Ese tiempo de desarrollo y de pruebas ya invertido, que hay que tirar y rehacer, es el costo. Por eso el enunciado del proyecto dice "no elijan valores para los límites sin consultarlos", y por eso dejamos esas dos reglas como pendientes en vez de inventarlas.  
Si el cliente responde que sí debe ser insensible a mayúsculas o que hay que recortar/validar el nombre, hay que modificar `is_available` y `register_loan`, y revisar todas las pruebas que ya asumen comparación exacta (por ejemplo `test_two_different_equipment_can_be_loaned_independently` o las de `test_example_*`), no solo agregar código nuevo.