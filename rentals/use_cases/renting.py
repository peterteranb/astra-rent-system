"""Casos de uso CU-04 a CU-07 y CU-16: renta en línea y en tienda, modificar y cancelar una reserva, y «Mis rentas».

Las vistas llaman a este módulo; aplica las reglas de rules.py y habla con la base. No lee la petición ni elige páginas.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.roles import CLIENT, OPERATOR, has_role

from .. import rules
from ..errors import (
    DeadlinePassedError,
    DebtPendingError,
    EquipmentNotAvailableError,
    InvalidModificationError,
    InvalidPeriodError,
    RentalStateError,
)
from ..models import Debt, Equipment, Rental
from ..services.events import log_event, logs_rejection
from ..services.formatting import client_debt_message, days_text, local_text, money_text, rental_state_message
from ..services.notifications import send_rental_cancelled, send_rental_confirmed
from ..statuses import PaymentMethod, RentalStatus
from .payments import debt_total_of, pending_debts_of

# ENT-54: el operador busca al cliente y lo elige de una lista corta, no de todos los clientes.
MAX_CLIENTS_FOUND = 10


@dataclass(frozen=True)
class ClientRentals:
    """Lo que ve el cliente en «Mis rentas»: sus rentas, sus deudas sin pagar y cuánto debe (CU-16)."""

    rentals: list[Rental]
    debts: list[Debt]
    debt_total: Decimal

    @property
    def debt_message(self):
        """El aviso de deuda que el cliente ve arriba de sus rentas."""
        return client_debt_message(self.debt_total)


def client_accounts():
    """Devuelve los clientes con la cuenta activa: a un cliente bloqueado no se le renta en la tienda (ENT-79)."""
    return get_user_model().objects.filter(role__code=CLIENT, is_active=True)


def find_clients(text):
    """Devuelve hasta MAX_CLIENTS_FOUND clientes cuyo usuario, nombre, apellido o correo contiene text (ENT-54)."""
    text = text.strip()
    # Una búsqueda vacía listaría a todos los clientes: el operador debe escribir algo.
    if not text:
        return client_accounts().none()
    matches = (
        Q(username__icontains=text)
        | Q(first_name__icontains=text)
        | Q(last_name__icontains=text)
        | Q(email__icontains=text)
    )
    return client_accounts().filter(matches).order_by("username")[:MAX_CLIENTS_FOUND]


def rentals_of(client):
    """Devuelve las rentas del cliente, la más reciente primero (CU-16)."""
    return Rental.objects.filter(client=client).select_related("equipment").order_by("-start_datetime")


def my_rentals(client) -> ClientRentals:
    """Devuelve las rentas del cliente con su estado y su pago, y lo que debe (CU-16, ENT-77)."""
    return ClientRentals(
        rentals=list(rentals_of(client)),
        debts=list(pending_debts_of(client)),
        debt_total=debt_total_of(client),
    )


def rentals_visible_to(user):
    """Devuelve las rentas que user puede abrir: el operador, todas; los demás, las suyas o las que registraron."""
    if has_role(user, OPERATOR):
        return Rental.objects.all()
    return Rental.objects.filter(Q(client=user) | Q(registered_by=user))


@logs_rejection("RENTAL_REJECTED")
def create_rental(client, equipment, start_datetime, end_datetime, registered_by=None) -> Rental:
    """Guarda una renta confirmada de un equipo y la devuelve (ENT-16: se confirma al instante).

    registered_by es el operador que la registró en la tienda, donde se paga en
    efectivo (ENT-70); es None si el cliente renta en línea y paga con el QR después.
    Siempre nace «Reservada»; si el cliente se la lleva al momento, el operador
    registra el recojo (ENT-91). Lanza un OperationRejectedError si se rompe una
    regla; entonces no se guarda nada.
    """
    # Las reglas comparan horas de reloj (18:00, 09:00): se trabaja en hora local.
    start = timezone.localtime(start_datetime)
    end = timezone.localtime(end_datetime)
    # El periodo no necesita la base: se revisa antes de bloquear ninguna fila.
    check_period(start, end)
    with transaction.atomic():
        check_client_has_no_debt(client, registered_by)
        # Bloquea la fila del equipo hasta el final: si dos clientes confirman a la
        # vez, el segundo espera aquí y ve la renta del primero (ENT-21: gana el primer clic).
        locked_equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        check_equipment_is_free(locked_equipment, start, end)
        rental = new_rental(client, locked_equipment, start, end, registered_by)
        rental.save()
    log_rental_created(rental)
    return rental


def new_rental(client, equipment, start, end, registered_by) -> Rental:
    """Arma la renta sin guardarla, con el precio de hoy; en la tienda nace pagada en efectivo (ENT-70, ENT-71)."""
    now = timezone.now()
    rental = Rental(
        client=client,
        equipment=equipment,
        start_datetime=start,
        end_datetime=end,
        daily_price=rules.daily_price_for(equipment.value),
        registered_by=registered_by,
    )
    if registered_by is not None:
        rental.paid_at = now
        rental.payment_method = PaymentMethod.CASH
    return rental


def log_rental_created(rental):
    """Escribe RENTAL_CREATED y, en la tienda, el cobro en efectivo y el correo de confirmación."""
    registered_by = rental.registered_by.username if rental.registered_by else "web"
    log_event(
        "RENTAL_CREATED",
        id=rental.pk,
        equipment=rental.equipment.inventory_id,
        client=rental.client.username,
        paid="yes" if rental.is_paid else "no",
        registered_by=registered_by,
    )
    # En línea, el correo sale cuando el cliente presiona un botón del QR (payments.pay_with_qr).
    if rental.registered_by is None:
        return
    log_event("PAYMENT_CASH", rental=rental.pk, amount=rental.total_price, received_by=registered_by)
    send_rental_confirmed(rental)


def check_period(start, end):
    """Lanza InvalidPeriodError si el periodo mismo rompe una regla, sea cual sea el equipo."""
    if not rules.is_pickup_date_allowed(start, timezone.localtime()):
        raise InvalidPeriodError("La fecha de recojo ya pasó. Elige hoy o un día siguiente.")
    if not rules.ends_after_start(start, end):
        raise InvalidPeriodError(
            "La fecha y hora de devolución debe ser posterior a la de recojo."
        )
    if not rules.is_within_max_duration(start, end):
        raise InvalidPeriodError(
            f"La renta no puede durar más de {rules.MAX_RENTAL_DAYS} días."
        )
    if not rules.is_pickup_time_allowed(start):
        raise InvalidPeriodError(
            f"El recojo debe ser desde las {rules.EARLIEST_PICKUP_TIME:%H:%M}."
        )
    if not rules.is_return_time_allowed(end):
        raise InvalidPeriodError(
            f"La devolución debe ser hasta las {rules.LATEST_RETURN_TIME:%H:%M}."
        )


def check_client_has_no_debt(client, registered_by):
    """Lanza DebtPendingError si el cliente debe algo: no renta ni en línea ni en tienda (ENT-77).

    El mensaje le habla al cliente en línea y al operador en la tienda.
    """
    total = debt_total_of(client)
    if not total:
        return
    if registered_by is None:
        raise DebtPendingError(client_debt_message(total))
    raise DebtPendingError(
        f"El cliente {client.username} tiene una deuda pendiente de {money_text(total)}. "
        "Cóbrala antes de registrar otra renta."
    )


def check_equipment_is_free(equipment, start, end, ignored=None):
    """Lanza EquipmentNotAvailableError si el equipo no se puede rentar en ese periodo (RF-01).

    ignored es la reserva que se está modificando: no choca consigo misma.
    """
    if not rules.is_rentable_status(equipment.status):
        raise EquipmentNotAvailableError(
            f"El equipo {equipment.inventory_id} no está disponible "
            f"(estado: {equipment.get_status_display()})."
        )
    # Las rentas vienen ordenadas por inicio (Rental.Meta): el primer choque es el
    # más próximo, y el mensaje nombra ese periodo.
    now = timezone.now()
    for rental in equipment.rentals.exclude(pk=getattr(ignored, "pk", None)):
        if not rental.occupies_equipment_at(now):
            continue
        if rules.periods_overlap(start, end, rental.start_datetime, rental.end_datetime):
            raise EquipmentNotAvailableError(busy_message(equipment, rental, start))


def busy_message(equipment, rental, start):
    """Dice cuándo está ocupado el equipo y, si esa renta empieza después, hasta cuándo está libre (ENT-36, ENT-51)."""
    busy_start = timezone.localtime(rental.start_datetime)
    message = (
        f"El equipo {equipment.inventory_id} está ocupado "
        f"del {local_text(rental.start_datetime)} al {local_text(rental.end_datetime)}."
    )
    # Solo una renta que empieza después del recojo pedido deja días libres antes,
    # y el equipo debe volver hasta las 09:00 de su primer día.
    if busy_start > start:
        message += (
            f" Está libre hasta el {busy_start:%d/%m/%Y} a las {rules.LATEST_RETURN_TIME:%H:%M}."
        )
    return message


@logs_rejection("MODIFY_REJECTED")
def modify_rental(rental, start_datetime, end_datetime, changed_by) -> Rental:
    """Cambia las fechas de una reserva por otras con la misma cantidad de días y la devuelve (ENT-81).

    El precio no cambia. Se revisan otra vez los horarios y la disponibilidad, sin
    contar la misma reserva. Lanza un OperationRejectedError si se rompe una regla.
    """
    start = timezone.localtime(start_datetime)
    end = timezone.localtime(end_datetime)
    check_period(start, end)
    with transaction.atomic():
        # Mismo orden que create_rental (primero el equipo, después la renta): dos
        # operaciones sobre el mismo equipo no se quedan esperando una a la otra.
        locked_equipment = Equipment.objects.select_for_update().get(pk=rental.equipment_id)
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        check_can_modify(locked_rental, changed_by, timezone.now())
        check_same_days(locked_rental, start, end)
        check_equipment_is_free(locked_equipment, start, end, ignored=locked_rental)
        locked_rental.start_datetime = start
        locked_rental.end_datetime = end
        locked_rental.save(update_fields=["start_datetime", "end_datetime"])
    log_event(
        "RENTAL_MODIFIED",
        id=locked_rental.pk,
        equipment=locked_rental.equipment.inventory_id,
        start=f"{start:%Y-%m-%dT%H:%M}",
        end=f"{end:%Y-%m-%dT%H:%M}",
        by=changed_by.username,
    )
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


@logs_rejection("CANCEL_REJECTED")
def cancel_rental(rental, cancelled_by, reason="") -> Rental:
    """Cancela una reserva todavía no recogida, guarda quién la canceló y avisa al cliente (ENT-80).

    Sus fechas quedan libres al instante, porque una renta cancelada ya no ocupa
    el equipo. El dinero se devuelve fuera del sistema (ENT-82). reason va en el
    correo y en el log; si falta, se dice quién canceló. Lanza un
    OperationRejectedError si no está «Reservada» o si el cliente llega tarde.
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
    log_event(
        "RENTAL_CANCELLED",
        id=locked_rental.pk,
        equipment=locked_rental.equipment.inventory_id,
        client=locked_rental.client.username,
        by=cancelled_by.username,
        reason=reason,
    )
    send_rental_cancelled(locked_rental, reason)
    return locked_rental


def cancel_reservations(rentals, cancelled_by, reason) -> list[Rental]:
    """Cancela las rentas de rentals todavía no recogidas, cada una con su correo y su línea de log, y las devuelve."""
    reservations = rentals.reserved_at(timezone.now())
    return [cancel_rental(reservation, cancelled_by, reason) for reservation in reservations]


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
    """Lanza un rechazo si user no puede modificar la renta en now (ENT-80)."""
    check_reservation_can_change(
        rental, user, now, "Ya no puedes modificar en línea; comunícate con la tienda."
    )


def check_reservation_can_change(rental, user, now, late_message):
    """Lanza RentalStateError si la renta no está «Reservada» y DeadlinePassedError si su cliente llega tarde.

    El plazo de 24 h es solo para el cliente; el personal la cambia hasta el recojo.
    """
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))
    if rental.client_id == user.pk and not rules.can_client_change(rental.start_datetime, now):
        raise DeadlinePassedError(late_message)
