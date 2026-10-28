"""Casos de uso CU-08 y CU-09: el operador entrega un equipo reservado y lo recibe de vuelta."""
from django.db import transaction
from django.utils import timezone

from ..errors import IncompleteReturnError, PaymentRequiredError, RentalStateError
from ..models import Rental
from ..services.events import log_event, logs_rejection
from ..services.formatting import money_text, rental_state_message
from ..statuses import DebtReason, EquipmentStatus, PaymentMethod, RentalStatus
from . import history
from .payments import charge_debt


def reservations_to_hand_over():
    """Devuelve las rentas «Reservadas» que el operador todavía puede entregar, la más próxima primero."""
    return (
        Rental.objects.reserved_at(timezone.now())
        .select_related("equipment", "client")
        .order_by("start_datetime")
    )


def rentals_to_receive():
    """Devuelve las rentas ni devueltas ni canceladas, la que vence primero arriba.

    Incluye las que nunca se recogieron (ENT-60: el sistema deja devolverlas).
    """
    return (
        Rental.objects.filter(returned_at__isnull=True, cancelled_at__isnull=True)
        .select_related("equipment", "client")
        .order_by("end_datetime")
    )


@logs_rejection("PICKUP_REJECTED")
def register_pickup(rental, staff_user, paid_now=False) -> Rental:
    """Guarda que el cliente se llevó el equipo ahora y qué operador lo entregó (ENT-56).

    Con el pago pendiente, solo se entrega si paid_now dice que el cliente pagó en
    efectivo en ese momento (ENT-68). Equipment.status no se toca: «Rentada» se
    calcula desde picked_up_at. Lanza RentalStateError si no está «Reservada» y
    PaymentRequiredError si falta el pago.
    """
    with transaction.atomic():
        # Bloquea la fila y la vuelve a leer: si dos operadores hacen clic a la
        # vez, el segundo espera aquí y ve el recojo del primero.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_pick_up(locked_rental, now)
        charged_now = not locked_rental.is_paid
        if charged_now:
            check_payment_received(locked_rental, paid_now)
            locked_rental.paid_at = now
            locked_rental.payment_method = PaymentMethod.CASH
        locked_rental.picked_up_at = now
        locked_rental.handed_over_by = staff_user
        locked_rental.save(
            update_fields=["paid_at", "payment_method", "picked_up_at", "handed_over_by"]
        )
    log_pickup(locked_rental, staff_user, charged_now)
    return locked_rental


def log_pickup(rental, staff_user, charged_now):
    """Escribe el cobro en efectivo, si se cobró al entregar, y después PICKUP_REGISTERED."""
    if charged_now:
        log_event(
            "PAYMENT_CASH", rental=rental.pk, amount=rental.total_price, received_by=staff_user.username
        )
    log_event(
        "PICKUP_REGISTERED",
        id=rental.pk,
        equipment=rental.equipment.inventory_id,
        client=rental.client.username,
        by=staff_user.username,
    )


def check_can_pick_up(rental, now):
    """Lanza RentalStateError si en now la renta no está «Reservada»."""
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))


def check_payment_received(rental, paid_now):
    """Lanza PaymentRequiredError si la renta tiene el pago pendiente y el operador no lo cobró."""
    if not paid_now:
        raise PaymentRequiredError(
            f"Falta el pago de {money_text(rental.total_price)} de esta renta. "
            "Cóbralo en efectivo o cancela la reserva si el cliente no paga."
        )


@logs_rejection("RETURN_REJECTED")
def register_return(rental, staff_user, note) -> Rental:
    """Guarda que el equipo volvió ahora y cómo llegó, lo manda a revisión y cobra el atraso (RF-09, RF-10).

    Desde las 12:01 del día de vencimiento crea una deuda de días de atraso ×
    precio por día (ENT-73). Lanza IncompleteReturnError sin observación y
    RentalStateError si la renta está cancelada o ya devuelta; entonces nada cambia.
    """
    note = note.strip()
    # La nota no necesita la base: se revisa antes de abrir la transacción.
    if not note:
        raise IncompleteReturnError("Escribe cómo llegó el equipo.")
    with transaction.atomic():
        # Bloquea la fila: dos operadores no pueden registrar la misma devolución.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        check_can_return(locked_rental)
        locked_rental.returned_at = timezone.now()
        locked_rental.received_by = staff_user
        locked_rental.return_note = note
        locked_rental.save(update_fields=["returned_at", "received_by", "return_note"])
        # ENT-60: una renta nunca recogida se puede devolver aunque el equipo ya esté en revisión.
        if locked_rental.equipment.status != EquipmentStatus.IN_REVIEW:
            history.change_status(
                locked_rental.equipment, EquipmentStatus.IN_REVIEW, staff_user, comment=note
            )
        log_event(
            "RETURN_REGISTERED",
            id=locked_rental.pk,
            equipment=locked_rental.equipment.inventory_id,
            client=locked_rental.client.username,
            by=staff_user.username,
            result=locked_rental.return_result,
            late_days=locked_rental.late_days,
        )
        if locked_rental.late_days:
            charge_debt(locked_rental, DebtReason.LATE_RETURN, locked_rental.late_charge)
    return locked_rental


def check_can_return(rental):
    """Lanza RentalStateError si la renta está cancelada o ya devuelta."""
    status = rental.status
    if status in (RentalStatus.CANCELLED, RentalStatus.RETURNED):
        raise RentalStateError(rental_state_message(rental, status))
