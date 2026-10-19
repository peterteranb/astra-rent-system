# Casos de uso y diagramas de secuencia del MVP

Un caso de uso por sección: primero **qué hace** (actor, pasos y rechazos), después **cómo lo hace el código**.

**Cómo leer los diagramas:**
- Flecha continua: una llamada.
- Flecha punteada: la respuesta.
- `alt` separa el camino de éxito del de rechazo.
- Todo rechazo ocurre **antes** de escribir en la base, así que la base no cambia.

**Lo que hace Django antes de cada vista, en todos los casos:**
1. El middleware carga la sesión.
2. Valida el token CSRF de los formularios.
3. Pone en `request.user` a la persona que inició sesión.
4. Después, el decorador de la vista revisa el rol: `@login_required` para el cliente, `@role_required(...)` para el personal.

| Caso de uso | Actor | Resultado | Código |
|---|---|---|---|
| [PRE-CU-01 Rentar en línea](#pre-cu-01--rentar-en-línea) | Cliente | Renta «Reservada» | `renting.create_rental` |
| [PRE-CU-02 Rentar en la tienda](#pre-cu-02--rentar-en-la-tienda) | Operador | Renta «Reservada» o «Rentada» | `renting.find_clients`, `renting.create_rental` |
| [PRE-CU-03 Entregar el equipo](#pre-cu-03--entregar-el-equipo) | Operador | Renta «Rentada» | `handover.register_pickup` |
| [PRE-CU-04 Registrar la devolución](#pre-cu-04--registrar-la-devolución) | Operador | Renta «Devuelta», equipo «En revisión» | `handover.register_return` |
| [PRE-CU-05 Revisar el equipo](#pre-cu-05--revisar-el-equipo) | Mantenimiento | Disponible, en reparación o baja | `review.review_equipment` |
| [PRE-CU-06 Cancelar una reserva](#pre-cu-06--cancelar-una-reserva) | Operador o admin | Renta «Cancelada» | `renting.cancel_rental` |

---

## PRE-CU-01 — Rentar en línea

| | |
|---|---|
| **Actor** | Cliente (`c01`) |
| **Disparador** | Elige un equipo del catálogo y unas fechas. |
| **Pasos** | 1. Elige el equipo en el catálogo, que muestra «Ocupado del … al …» (hasta 3 periodos) o «Libre» (`renting.catalog_entries`). 2. Escribe el recojo (desde las 18:00) y la devolución (hasta las 09:00). 3. Confirma. 4. Ve la confirmación. |
| **Rechazos** | Fechas inválidas: se queda en el formulario con la causa. Fechas ocupadas: vuelve al catálogo con «El equipo EQ-01 está ocupado del … al ….» y, si esa renta empieza después del recojo pedido, «Está libre hasta el … a las 09:00.». |
| **Reglas** | PRE-RF-01 (gana el primero, sin cruces), ENT-19, ENT-52, ENT-64. |

```mermaid
sequenceDiagram
    actor C as Cliente
    participant N as Navegador
    participant MW as Middleware de Django<br/>(sesión, CSRF, usuario)
    participant V as Vista<br/>views.renting.rent_equipment
    participant U as Caso de uso<br/>renting.create_rental
    participant R as Reglas<br/>rules.py
    participant DB as PostgreSQL

    C->>N: Elige fechas y presiona «Rentar»
    N->>MW: POST /equipment/EQ-01/rent/
    MW->>V: request con c01
    V->>V: @login_required y RentalForm (fechas → hora de La Paz)
    V->>U: create_rental(c01, EQ-01, inicio, fin)
    U->>R: check_period: ¿fin > inicio?, ¿≤ 5 días?, ¿recojo ≥ 18:00?, ¿devolución ≤ 09:00?
    alt periodo inválido
        R-->>U: no cumple
        U-->>V: InvalidPeriodError / OutsideRentalHoursError
        V-->>N: mismo formulario con la causa
    else periodo válido
        U->>DB: BEGIN · SELECT equipo FOR UPDATE (bloquea EQ-01)
        U->>DB: SELECT rentas de EQ-01 (por fecha de inicio)
        U->>U: check_equipment_is_free: occupies_equipment_at(ahora) («Reservada» o «Rentada»)
        U->>R: periods_overlap con cada renta que sigue ocupando el equipo
        alt fechas ocupadas
            U->>DB: ROLLBACK (no se guardó nada)
            U-->>V: EquipmentNotAvailableError (busy_message)
            V-->>N: 302 al catálogo con «ocupado del … al …. Está libre hasta …»
        else fechas libres
            U->>DB: INSERT renta · COMMIT
            U-->>V: renta «Reservada»
            V-->>N: 302 a la confirmación
        end
    end
```

**Por qué se bloquea la fila del equipo:** si dos clientes confirman a la vez, el segundo espera a que termine el primero, ve su renta y recibe el rechazo. Así «gana el primero que hizo clic» (ENT-21).

---

## PRE-CU-02 — Rentar en la tienda

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Disparador** | Un cliente llega a la tienda. |
| **Pasos** | 1. Abre «Renta en tienda» y busca al cliente por nombre, apellido, usuario o correo. 2. Lo elige. 3. Elige el equipo y las fechas. 4. Si el cliente se lo lleva en ese momento, marca «Se lo lleva ahora». 5. Confirma. 6. Ve la confirmación con «Registrada por: op01». |
| **Rechazos** | Los mismos de PRE-CU-01: las reglas son iguales para todos. |
| **Reglas** | ENT-53, ENT-54, ENT-57. La renta queda «Registrada por: op01». Con «Se lo lleva ahora» nace «Rentada». |

```mermaid
sequenceDiagram
    actor O as Operador
    participant N as Navegador
    participant MW as Middleware de Django<br/>(sesión, CSRF, usuario)
    participant V as Vista<br/>views.renting.walk_in_rental
    participant U as Caso de uso<br/>renting.py
    participant DB as PostgreSQL

    O->>N: Escribe «perez» y busca
    N->>MW: GET /staff/walk-in/?q=perez
    MW->>V: request con op01
    V->>V: @role_required(OPERATOR)
    V->>U: find_clients("perez")
    U->>DB: SELECT clientes por usuario, nombre, apellido o correo (sin personal, operador ni mantenimiento, máx. 10)
    U-->>V: lista de clientes
    V-->>N: resultados y WalkInRentalForm
    O->>N: Elige a c01, el equipo, las fechas y «Se lo lleva ahora»
    N->>MW: POST /staff/walk-in/?q=perez
    MW->>V: request con op01
    V->>V: WalkInRentalForm (cliente, equipo, fechas → hora de La Paz, «Se lo lleva ahora»)
    V->>U: create_rental(c01, EQ-02, inicio, fin, registered_by=op01, picked_up_now=True)
    Note over U,DB: Mismas validaciones y bloqueo que PRE-CU-01
    alt rechazo
        U-->>V: OperationRejectedError (causa)
        V-->>N: formulario con la causa
    else éxito
        U->>DB: INSERT renta (registered_by, picked_up_at, handed_over_by) · COMMIT
        U-->>V: renta «Rentada»
        V-->>N: 302 a la confirmación con «Registrada por: op01»
    end
```

---

## PRE-CU-03 — Entregar el equipo

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Disparador** | El cliente llega a recoger. |
| **Pasos** | 1. Abre «Reservas por entregar». 2. Presiona «Registrar recojo» en la renta. 3. Ve «Recojo registrado: EQ-01 entregado a c01.». |
| **Rechazos** | Ya entregada (con la fecha del primer recojo), reserva vencida (después de las 12:00 del día siguiente) o cancelada. |
| **Reglas** | ENT-56 («todo inventariado»), ENT-59. El estado del equipo **no** cambia: «Rentada» se calcula desde la renta. |

```mermaid
sequenceDiagram
    actor O as Operador
    participant N as Navegador
    participant MW as Middleware de Django<br/>(sesión, CSRF, usuario)
    participant V as Vista<br/>views.handover.pickup_reservation
    participant U as Caso de uso<br/>handover.register_pickup
    participant DB as PostgreSQL

    O->>N: «Registrar recojo»
    N->>MW: POST /staff/reservations/7/pickup/
    MW->>V: request con op01
    V->>V: @role_required(OPERATOR) y @require_POST
    V->>U: register_pickup(renta 7, op01)
    U->>DB: BEGIN · SELECT renta FOR UPDATE (bloquea la renta)
    U->>U: check_can_pick_up: ¿cancelada?, ¿ya entregada?, ¿vencida?
    alt se puede entregar
        U->>DB: UPDATE picked_up_at = ahora, handed_over_by = op01 · COMMIT
        U-->>V: renta «Rentada»
        V-->>N: 302 a la lista con «Recojo registrado…»
    else cancelada, ya entregada o vencida
        U->>DB: ROLLBACK (no se guardó nada)
        U-->>V: RentalCancelledError / AlreadyPickedUpError / ReservationExpiredError
        V-->>N: 302 a la lista con la causa
    end
```

---

## PRE-CU-04 — Registrar la devolución

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Disparador** | El cliente trae el equipo. |
| **Pasos** | 1. Abre «Devoluciones». 2. Elige la renta. 3. Escribe cómo llegó el equipo. 4. Confirma. 5. Ve «Devolución registrada: EQ-01 recibido de c01. A tiempo.» (o «Con multa.» / «Se cobra un día más.»). |
| **Rechazos** | Sin observación, ya devuelta (con la fecha) o cancelada. Una renta que **nunca se recogió sí** se puede devolver (ENT-60). |
| **Reglas** | ENT-43, ENT-63, ENT-65: hasta las 09:00 a tiempo, hasta las 12:00 con multa y desde las 12:01 un día más, siempre contra las 09:00 del día de vencimiento. |

```mermaid
sequenceDiagram
    actor O as Operador
    participant N as Navegador
    participant MW as Middleware de Django<br/>(sesión, CSRF, usuario)
    participant V as Vista<br/>views.handover.return_rental
    participant U as Caso de uso<br/>handover.register_return
    participant H as history.change_status
    participant DB as PostgreSQL

    O->>N: Escribe «pata floja» y confirma
    N->>MW: POST /staff/returns/7/
    MW->>V: request con op01
    V->>V: @role_required(OPERATOR) y ReturnForm
    V->>U: register_return(renta 7, op01, nota)
    U->>U: ¿nota vacía? (no necesita la base)
    alt nota vacía
        U-->>V: IncompleteReturnError
        V-->>N: mismo formulario con «Escribe cómo llegó el equipo.»
    else hay nota
        U->>DB: BEGIN · SELECT renta FOR UPDATE
        U->>U: check_can_return: ¿cancelada?, ¿ya devuelta?
        alt cancelada o ya devuelta
            U->>DB: ROLLBACK (no se guardó nada)
            U-->>V: RentalCancelledError / AlreadyReturnedError
            V-->>N: mismo formulario con la causa
        else se puede devolver
            U->>DB: UPDATE returned_at, received_by, return_note
            U->>H: change_status(equipo, EN REVISIÓN, op01, nota)
            H->>DB: SELECT equipo FOR UPDATE · UPDATE status · INSERT historial
            U->>DB: COMMIT (todo junto)
            U-->>V: renta «Devuelta» y return_result
            V-->>N: 302 a la lista con «… A tiempo / Con multa / Se cobra un día más»
        end
    end
```

---

## PRE-CU-05 — Revisar el equipo

| | |
|---|---|
| **Actor** | Mantenimiento (`mt01`) |
| **Disparador** | Hay equipos «En revisión» o «En reparación». |
| **Pasos** | 1. Abre «Mantenimiento». 2. Elige el nuevo estado de un equipo. 3. Escribe un comentario opcional. 4. Guarda. 5. Ve «EQ-01 ahora está «Disponible».». |
| **Rechazos** | Un estado que no es resultado de una revisión, o un equipo dado de baja (la baja es definitiva). |
| **Reglas** | ENT-34, ENT-49. Desde revisión: disponible, reparación o baja. Desde reparación: disponible (o baja). Cada cambio queda en el historial. |

```mermaid
sequenceDiagram
    actor M as Mantenimiento
    participant N as Navegador
    participant MW as Middleware de Django<br/>(sesión, CSRF, usuario)
    participant V as Vista<br/>views.review.review_unit
    participant U as Caso de uso<br/>review.review_equipment
    participant H as history.change_status
    participant DB as PostgreSQL

    M->>N: Elige «Disponible» y guarda
    N->>MW: POST /maintenance/EQ-01/
    MW->>V: request con mt01
    V->>V: @role_required(MAINTENANCE) y @require_POST
    V->>U: review_equipment(EQ-01, mt01, disponible, comentario)
    U->>U: check_review_result: ¿disponible, reparación o baja?
    alt estado no permitido
        U-->>V: InvalidStatusChangeError
        V-->>N: 302 a la lista con la causa
    else permitido
        U->>H: change_status(EQ-01, disponible, mt01, comentario)
        H->>DB: BEGIN · SELECT equipo FOR UPDATE
        H->>H: ¿está de baja?
        alt de baja
            H->>DB: ROLLBACK
            H-->>V: InvalidStatusChangeError
            V-->>N: 302 con «está dado de baja, su estado ya no puede cambiar.»
        else se puede cambiar
            H->>DB: UPDATE status · INSERT historial · COMMIT
            H-->>V: cambio guardado
            V-->>N: 302 con «EQ-01 ahora está «Disponible».»
        end
    end
```

---

## PRE-CU-06 — Cancelar una reserva

| | |
|---|---|
| **Actor** | Operador desde «Reservas por entregar», o admin desde su panel |
| **Disparador** | El cliente avisa que no vendrá, o hay un problema (por ejemplo, el equipo se rompió antes, ENT-47). |
| **Pasos** | 1. Presiona «Cancelar» en la reserva. 2. Ve «Reserva cancelada: EQ-01 de c01.». |
| **Rechazos** | Solo se cancela una reserva «Reservada». Si ya fue entregada, devuelta o cancelada, el mensaje dice cuándo; si venció, «La reserva de EQ-01 venció a las 12:00.». |
| **Reglas** | ENT-55 («hacer y deshacer reservas»). Las fechas quedan libres para otros. |

```mermaid
sequenceDiagram
    actor O as Operador
    participant N as Navegador
    participant MW as Middleware de Django<br/>(sesión, CSRF, usuario)
    participant V as Vista<br/>views.renting.cancel_reservation
    participant U as Caso de uso<br/>renting.cancel_rental
    participant DB as PostgreSQL

    O->>N: «Cancelar»
    N->>MW: POST /staff/reservations/7/cancel/
    MW->>V: request con op01
    V->>V: @role_required(OPERATOR) y @require_POST
    V->>U: cancel_rental(renta 7, op01)
    U->>DB: BEGIN · SELECT renta FOR UPDATE
    U->>U: check_can_cancel: ¿status_at(ahora) es «Reservada»?
    alt entregada, devuelta, cancelada o vencida
        U->>DB: ROLLBACK (no se guardó nada)
        U-->>V: RentalNotCancellableError (con la causa)
        V-->>N: 302 a la lista con la causa
    else reservada
        U->>DB: UPDATE cancelled_at, cancelled_by · COMMIT
        U-->>V: renta «Cancelada»
        V-->>N: 302 a la lista con «Reserva cancelada: EQ-01 de c01.»
    end
```

---

## Qué tabla cambia cada botón

| Botón | Función | Tabla: columnas que cambian |
|---|---|---|
| Rentar (cliente u operador) | `renting.create_rental` | `rentals_rental`: fila nueva (con «Se lo lleva ahora», también `picked_up_at` y `handed_over_by`) |
| Registrar recojo | `handover.register_pickup` | `rentals_rental`: `picked_up_at`, `handed_over_by` |
| Registrar devolución | `handover.register_return` | `rentals_rental`: `returned_at`, `received_by`, `return_note` |
| ↳ (dentro de la devolución) | `history.change_status` | `rentals_equipment`: `status` · `rentals_statuschange`: fila nueva |
| Guardar (mantenimiento) | `review.review_equipment` → `history.change_status` | `rentals_equipment`: `status` · `rentals_statuschange`: fila nueva |
| Cancelar | `renting.cancel_rental` | `rentals_rental`: `cancelled_at`, `cancelled_by` |
