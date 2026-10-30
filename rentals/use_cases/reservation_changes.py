"""Cambios a una reserva todavía no recogida: modificar sus fechas (CU-06) y cancelarla (CU-07).

También la cancelación automática: cuando el equipo sale de servicio (CU-10, CU-13) o la cuenta del cliente se desactiva (D-27).
"""
from django.db import transaction
from django.utils import timezone

from .. import rules
from ..errors import DeadlinePassedError, InvalidModificationError, RentalStateError
from ..models import Equipment, Rental
from ..services.events import log_event, logs_rejection, period_text, rental_context
from ..services.formatting import days_text, local_text, rental_state_message
from ..services.notifications import send_rental_cancelled, send_rental_modified
from ..statuses import RentalStatus
from .renting import check_equipment_is_free, check_period

DEACTIVATED_REASON = "La cuenta fue desactivada."


def attempted_modification(rental, start_datetime, end_datetime, changed_by):
    """La reserva con las fechas que se pidieron, para el log del rechazo."""
    return {**rental_context(rental, changed_by.username), "period": period_text(start_datetime, end_datetime)}


@logs_rejection("MODIFY_REJECTED", attempted_modification)
def modify_rental(rental, start_datetime, end_datetime, changed_by) -> Rental:
    """Cambia las fechas de una reserva por otras con la misma cantidad de días y la devuelve (ENT-81).

    El precio no cambia. Si la cambió el personal, el cliente recibe las fechas nuevas por correo (ENT-95).
    """
    start = timezone.localtime(start_datetime)
    end = timezone.localtime(end_datetime)
    check_period(start, end)
    with transaction.atomic():
        # Mismo orden que create_rental (equipo y después renta): dos operaciones no se esperan una a la otra.
        locked_equipment = Equipment.objects.select_for_update().get(pk=rental.equipment_id)
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        check_can_modify(locked_rental, changed_by, timezone.now())
        check_same_days(locked_rental, start, end)
        check_equipment_is_free(locked_equipment, start, end, ignored=locked_rental)
        locked_rental.start_datetime = start
        locked_rental.end_datetime = end
        locked_rental.save(update_fields=["start_datetime", "end_datetime"])
    log_event("RENTAL_MODIFIED", **rental_context(locked_rental, changed_by.username))
    if changed_by.pk != locked_rental.client_id:
        send_rental_modified(locked_rental)
    return locked_rental


def check_same_days(rental, start, end):
    """Lanza InvalidModificationError si el periodo nuevo no tiene los mismos días que la reserva (ENT-81)."""
    days = rental.rental_days
    if rules.rental_days(start, end) == days:
        return
    raise InvalidModificationError(
        f"La reserva es de {days_text(days)}. Elige fechas con la misma cantidad de días; "
        "para cambiarla, cancela y renta de nuevo."
    )


def attempted_cancellation(rental, cancelled_by, reason=""):
    """La reserva que se quiso cancelar, para el log del rechazo."""
    return rental_context(rental, cancelled_by.username)


@logs_rejection("CANCEL_REJECTED", attempted_cancellation)
def cancel_rental(rental, cancelled_by, reason="") -> Rental:
    """Cancela una reserva todavía no recogida, guarda quién la canceló y avisa al cliente (ENT-80).

    Sus fechas quedan libres al instante y el dinero se devuelve fuera del sistema (ENT-82).
    reason va en el correo y en el log; si falta, se dice quién canceló.
    """
    with transaction.atomic():
        # Bloquea la fila: un recojo y una cancelación a la vez no se guardan los dos.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_cancel(locked_rental, cancelled_by, now)
        locked_rental.cancelled_at = now
        locked_rental.cancelled_by = cancelled_by
        locked_rental.save(update_fields=["cancelled_at", "cancelled_by"])
    reason = reason or default_cancellation_reason(locked_rental, cancelled_by)
    log_event("RENTAL_CANCELLED", **rental_context(locked_rental, cancelled_by.username), reason=reason)
    send_rental_cancelled(locked_rental, reason)
    return locked_rental


def cancel_reservations(rentals, cancelled_by, reason) -> list[Rental]:
    """Cancela las rentas de rentals todavía no recogidas, cada una con su correo y su línea de log, y las devuelve."""
    reservations = rentals.reserved_at(timezone.now())
    return [cancel_rental(reservation, cancelled_by, reason) for reservation in reservations]


def cancel_reservations_of_deactivated(client, cancelled_by) -> list[Rental]:
    """Cancela las reservas no recogidas de un cliente desactivado; las rentas que tiene en la mano siguen (D-27)."""
    return cancel_reservations(Rental.objects.filter(client=client), cancelled_by, DEACTIVATED_REASON)


def default_cancellation_reason(rental, cancelled_by):
    """Dice quién canceló, para el correo del cliente."""
    if rental.client_id == cancelled_by.pk:
        return "Cancelaste tu reserva."
    return "La tienda canceló tu reserva."


def check_can_cancel(rental, user, now):
    """Lanza un rechazo si user no puede cancelar la renta en now (ENT-80)."""
    check_reservation_can_change(
        rental, user, now, "Ya no puedes cancelar en línea; comunícate con la tienda."
    )


def check_can_modify(rental, user, now):
    """Lanza un rechazo si user no puede modificar la renta en now: el cliente hasta 24 h antes, el personal hasta el inicio (ENT-95)."""
    check_reservation_can_change(
        rental, user, now, "Ya no puedes modificar en línea; comunícate con la tienda."
    )
    if not rules.can_staff_modify(rental.start_datetime, now):
        raise DeadlinePassedError(
            f"La reserva de {rental.equipment.inventory_id} ya empezó el {local_text(rental.start_datetime)}; "
            "ya no se puede modificar."
        )


def check_reservation_can_change(rental, user, now, late_message):
    """Lanza RentalStateError si la renta no está «Reservada» y DeadlinePassedError si su cliente llega tarde.

    El plazo de 24 h es solo para el cliente; el personal la cancela hasta el recojo.
    """
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))
    if rental.client_id == user.pk and not rules.can_client_change(rental.start_datetime, now):
        raise DeadlinePassedError(late_message)
