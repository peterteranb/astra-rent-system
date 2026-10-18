# Diagramas de secuencia

## Entregar y devolver

```mermaid
sequenceDiagram
    actor Op as Operador
    participant Nav as Navegador
    participant MW as Middleware Django<br/>(sesión, CSRF, usuario)
    participant V as views.handover.return_rental
    participant H as handover.register_return
    participant Hist as history.change_status
    participant DB as Base de datos

    Op->>Nav: Escribe la nota y pulsa "Registrar devolución"
    Nav->>MW: POST /staff/returns/{id}/ (cookie de sesión + csrfmiddlewaretoken)
    MW->>MW: SessionMiddleware, CsrfViewMiddleware, AuthenticationMiddleware
    MW->>V: return_rental(request, rental_id)
    V->>V: @role_required(OPERATOR): sin rol responde 403
    V->>DB: get_object_or_404(Rental)
    V->>V: ReturnForm.is_valid()
    V->>H: register_return(rental, request.user, note)
    H->>DB: BEGIN + SELECT rentals_rental FOR UPDATE
    H->>H: check_can_return(locked_rental)
    alt returned_at vacío: éxito
        H->>DB: UPDATE rentals_rental (returned_at, received_by, return_note)
        H->>Hist: change_status(equipment, IN_REVIEW, staff_user, comment=note)
        Hist->>DB: SELECT rentals_equipment FOR UPDATE
        Hist->>Hist: check_status_can_change(locked_equipment)
        Hist->>DB: UPDATE rentals_equipment.status = in_review
        Hist->>DB: INSERT rentals_statuschange
        H->>DB: COMMIT
        H-->>V: locked_rental
        V-->>Nav: 302 a staff_returns + messages.success
    else returned_at con fecha: devolución repetida
        H->>DB: ROLLBACK al salir de atomic (no se hizo ningún UPDATE)
        H-->>V: raise AlreadyReturnedError
        V-->>Nav: 200 return_form.html con form.add_error
    end
    Nav-->>Op: Muestra el mensaje
```

| Botón | Función | Tabla y columna que cambia |
|---|---|---|
| Registrar recojo | `handover.register_pickup` | `rentals_rental`: `picked_up_at`, `handed_over_by` |
| Registrar devolución | `handover.register_return` | `rentals_rental`: `returned_at`, `received_by`, `return_note` |
| Registrar devolución | `history.change_status` | `rentals_equipment`: `status`; `rentals_statuschange`: fila nueva |
