"""Casos de uso CU-08 y CU-09: el operador entrega un equipo reservado y lo recibe de vuelta."""
from django.db import transaction
from django.utils import timezone

from .. import rules
from ..errors import EquipmentNotAvailableError, IncompleteReturnError, PaymentRequiredError, RentalStateError
from ..models import Equipment, Rental
from ..services.events import log_event, logs_rejection, rental_context
from ..services.formatting import money_text, rental_state_message
from ..statuses import DebtReason, EquipmentStatus, PaymentMethod, RentalStatus
from . import history
from .payments import charge_debt


# ENT-100: por defecto lo último primero; para atender en la tienda también sirve el orden por fecha.
ORDER_RECENT = "recent"
ORDER_BY_DATE = "date"


def reservations_to_hand_over(order=ORDER_RECENT):
    """Devuelve las rentas «Reservadas» que el operador todavía puede entregar, la más nueva o la de recojo más próximo primero."""
    return (
        Rental.objects.reserved_at(timezone.now())
        .select_related("equipment", "client")
        .order_by(order_field(order, "start_datetime"))
    )


def rentals_to_receive(order=ORDER_RECENT):
    """Devuelve las rentas «Rentadas», la más nueva o la que vence primero arriba: solo esas se devuelven (ENT-93)."""
    return Rental.objects.rented().select_related("equipment", "client").order_by(order_field(order, "end_datetime"))


def order_field(order, date_field):
    """Devuelve por qué campo se ordena: date_field si se pidió por fecha; si no, la renta más nueva primero."""
    if order == ORDER_BY_DATE:
        return date_field
    return "-created_at"


def attempted_pickup(rental, staff_user, paid_now=False):
    """La renta que se quiso entregar, para el log del rechazo."""
    return rental_context(rental, staff_user.username)


@logs_rejection("PICKUP_REJECTED", attempted_pickup)
def register_pickup(rental, staff_user, paid_now=False) -> Rental:
    """Guarda que el cliente se llevó el equipo ahora y qué operador lo entregó (ENT-56).

    Con el pago pendiente, solo se entrega si paid_now dice que el cliente pagó en
    efectivo en ese momento (ENT-68). Equipment.status no se toca: «Rentada» se
    calcula desde picked_up_at. Lanza RentalStateError si no está «Reservada»,
    EquipmentNotAvailableError si el equipo no está «Disponible» y
    PaymentRequiredError si falta el pago.
    """
    with transaction.atomic():
        # Primero el equipo y después la renta, como create_rental: así un cambio de
        # estado y un recojo a la vez no se esperan uno al otro. Si dos operadores
        # hacen clic a la vez, el segundo espera aquí y ve el recojo del primero.
        locked_equipment = Equipment.objects.select_for_update().get(pk=rental.equipment_id)
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_pick_up(locked_rental, now)
        check_equipment_can_go_out(locked_equipment)
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
    context = rental_context(rental, staff_user.username)
    if charged_now:
        log_event("PAYMENT_CASH", **context)
    log_event("PICKUP_REGISTERED", **context)


def check_can_pick_up(rental, now):
    """Lanza RentalStateError si en now la renta no está «Reservada»."""
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))


def check_equipment_can_go_out(equipment):
    """Lanza EquipmentNotAvailableError si el equipo no está «Disponible», por ejemplo en revisión."""
    if rules.is_rentable_status(equipment.status):
        return
    raise EquipmentNotAvailableError(
        f"El equipo {equipment.inventory_id} está {equipment.get_status_display().lower()}. "
        "Espera a que mantenimiento lo revise o cancela la reserva."
    )


def check_payment_received(rental, paid_now):
    """Lanza PaymentRequiredError si la renta tiene el pago pendiente y el operador no lo cobró."""
    if not paid_now:
        raise PaymentRequiredError(
            f"Falta el pago de {money_text(rental.total_price)} de esta renta. "
            "Cóbralo en efectivo o cancela la reserva si el cliente no paga."
        )


def attempted_return(rental, staff_user, note):
    """La renta que se quiso devolver, para el log del rechazo."""
    return rental_context(rental, staff_user.username)


@logs_rejection("RETURN_REJECTED", attempted_return)
def register_return(rental, staff_user, note) -> Rental:
    """Guarda que el equipo volvió ahora y cómo llegó, lo manda a revisión y cobra el atraso (RF-09, RF-10).

    Desde las 12:01 del día de vencimiento crea una deuda de días de atraso ×
    precio por día (ENT-73). Lanza IncompleteReturnError sin observación y
    RentalStateError si la renta no está «Rentada» (ENT-93); entonces nada cambia.
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
        # Si mantenimiento ya le cambió el estado mientras estaba afuera (ENT-90), se
        # respeta: la devolución no puede fallar por eso (D-28).
        if rules.is_rentable_status(locked_rental.equipment.status):
            history.change_status(
                locked_rental.equipment, EquipmentStatus.IN_REVIEW, staff_user, comment=note
            )
        log_event(
            "RETURN_REGISTERED",
            **rental_context(locked_rental, staff_user.username),
            result=locked_rental.return_result,
            late_days=locked_rental.late_days,
        )
        if locked_rental.late_days:
            charge_debt(locked_rental, DebtReason.LATE_RETURN, locked_rental.late_charge, staff_user)
    return locked_rental


def check_can_return(rental):
    """Lanza RentalStateError si la renta no está «Rentada»: solo se devuelve un equipo que salió (ENT-93)."""
    status = rental.status
    if status == RentalStatus.RENTED:
        return
    if status in (RentalStatus.RESERVED, RentalStatus.NOT_PICKED_UP):
        raise RentalStateError(
            f"La renta de {rental.equipment.inventory_id} nunca se entregó: solo se devuelve una renta «Rentada»."
        )
    raise RentalStateError(rental_state_message(rental, status))
