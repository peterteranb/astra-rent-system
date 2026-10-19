## Revisar y admin

Mantenimiento revisa un equipo devuelto desde `/maintenance/` (D2). El cambio de estado siempre pasa por `history.change_status`, que lo guarda junto con su historial (ENT-34).

### Éxito: un equipo en revisión pasa a disponible

```mermaid
sequenceDiagram
    autonumber
    actor M as Mantenimiento
    participant N as Navegador
    participant W as Middleware
    participant V as Vista views/review.py
    participant R as review.review_equipment
    participant H as history.change_status
    participant DB as Base de datos

    M->>N: Elige «Disponible», escribe un comentario y presiona «Guardar»
    N->>W: POST /maintenance/EQ-03/ con status, comment, token CSRF y cookie de sesión
    W->>W: Carga la sesión, identifica al usuario y valida el token CSRF
    W->>V: review_unit(request, "EQ-03")
    V->>V: role_required(MAINTENANCE) y require_POST
    V->>DB: SELECT del equipo con inventory_id EQ-03
    DB-->>V: Equipo EQ-03 en revisión
    V->>R: review_equipment(equipo, usuario, "available", comentario)
    R->>R: check_review_result acepta "available"
    R->>H: change_status(equipo, "available", usuario, comentario)
    H->>DB: BEGIN y SELECT FOR UPDATE sobre el equipo
    DB-->>H: Fila bloqueada con estado actual "in_review"
    H->>H: check_status_can_change confirma que no está dado de baja
    H->>DB: UPDATE del equipo con status "available"
    H->>DB: INSERT en el historial con equipo, de, a, quién y comentario
    H->>DB: COMMIT
    H-->>R: StatusChange
    R-->>V: StatusChange
    V->>V: messages.success con el equipo y su nuevo estado
    V-->>N: 302 a /maintenance/
    N->>V: GET /maintenance/
    V->>DB: SELECT de los equipos en revisión o en reparación
    DB-->>V: Lista sin EQ-03
    V-->>N: 200 con maintenance.html y el mensaje
    N-->>M: Muestra «EQ-03 ahora está «Disponible».» y la lista actualizada
```

### Rechazo: un equipo dado de baja no vuelve a disponible

La baja es definitiva. Esto ocurre si la página ya estaba abierta cuando otra persona dio de baja el equipo, o si alguien envía el formulario a mano.

```mermaid
sequenceDiagram
    autonumber
    actor M as Mantenimiento
    participant N as Navegador
    participant W as Middleware
    participant V as Vista views/review.py
    participant R as review.review_equipment
    participant H as history.change_status
    participant DB as Base de datos

    M->>N: Elige «Disponible» para EQ-03 y presiona «Guardar»
    N->>W: POST /maintenance/EQ-03/ con status, comment, token CSRF y cookie de sesión
    W->>V: review_unit(request, "EQ-03")
    V->>DB: SELECT del equipo con inventory_id EQ-03
    DB-->>V: Equipo EQ-03
    V->>R: review_equipment(equipo, usuario, "available", comentario)
    R->>R: check_review_result acepta "available"
    R->>H: change_status(equipo, "available", usuario, comentario)
    H->>DB: BEGIN y SELECT FOR UPDATE sobre el equipo
    DB-->>H: Fila bloqueada con estado actual "retired"
    H->>H: check_status_can_change lanza InvalidStatusChangeError
    H->>DB: ROLLBACK, no se guarda nada
    H--xR: InvalidStatusChangeError
    R--xV: InvalidStatusChangeError
    V->>V: Atrapa OperationRejectedError y llama a messages.error con la causa
    V-->>N: 302 a /maintenance/
    N->>V: GET /maintenance/
    V-->>N: 200 con maintenance.html y el mensaje de error
    N-->>M: Muestra la causa del rechazo
```

El mensaje que ve mantenimiento es «El equipo EQ-03 está dado de baja; su estado ya no puede cambiar.». El equipo y el historial quedan igual que antes del intento.

### Botón, función y datos que cambian

| Botón | Función | Tabla y columna que cambia |
|---|---|---|
| «Guardar» (`/maintenance/`) | `views.review.review_unit` → `review.review_equipment` → `history.change_status` | `rentals_equipment.status`, y una fila nueva en `rentals_statuschange` (`equipment_id`, `old_status`, `new_status`, `changed_by_id`, `changed_at`, `comment`) |
| «Marcar disponible» (admin, Equipos) | `EquipmentAdmin.mark_available` → `change_selected` → `history.change_status` | `rentals_equipment.status` = `available` y una fila en `rentals_statuschange` |
| «Mandar a reparación» (admin, Equipos) | `EquipmentAdmin.send_to_repair` → `change_selected` → `history.change_status` | `rentals_equipment.status` = `in_repair` y una fila en `rentals_statuschange` |
| «Dar de baja» (admin, Equipos) | `EquipmentAdmin.retire` → `change_selected` → `history.change_status` | `rentals_equipment.status` = `retired` y una fila en `rentals_statuschange` |
| «Cancelar reserva» (admin, Rentas) | `RentalAdmin.cancel_reservations` → `renting.cancel_rental` | `rentals_rental.cancelled_at` y `rentals_rental.cancelled_by_id` |
