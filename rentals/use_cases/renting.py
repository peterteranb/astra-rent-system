"""Rentar: la renta en línea (CU-04) y en la tienda (CU-05), buscar clientes para la tienda y «Mis rentas» (CU-16).

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
from ..errors import DebtPendingError, EquipmentNotAvailableError, InvalidPeriodError
from ..models import Debt, Equipment, Rental
from ..services.events import log_event, logs_rejection, rental_context
from ..services.formatting import client_debt_message, local_text, money_text
from ..services.notifications import send_rental_confirmed
from ..statuses import PaymentMethod
from .debts import debt_total_of, pending_debts_of

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
    """Devuelve hasta MAX_CLIENTS_FOUND clientes cuyo usuario, nombre, apellido o correo contiene text, la cuenta más nueva primero (ENT-54, ENT-100)."""
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
    return client_accounts().filter(matches).order_by("-date_joined", "username")[:MAX_CLIENTS_FOUND]


def rentals_of(client):
    """Devuelve las rentas del cliente, la creada más recientemente primero (CU-16, ENT-100)."""
    return Rental.objects.filter(client=client).select_related("equipment").order_by("-created_at")


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


def acting_username(client, registered_by):
    """Devuelve quién hizo la renta: el operador en la tienda o el cliente en línea."""
    return (registered_by or client).username


def attempted_rental(client, equipment, start_datetime, end_datetime, registered_by=None):
    """Lo que se intentó rentar, para el log del rechazo: todavía no tiene id ni precio."""
    rental = Rental(client=client, equipment=equipment, start_datetime=start_datetime, end_datetime=end_datetime)
    return rental_context(rental, acting_username(client, registered_by))


@logs_rejection("RENTAL_REJECTED", attempted_rental)
def create_rental(client, equipment, start_datetime, end_datetime, registered_by=None) -> Rental:
    """Guarda una renta confirmada de un equipo y la devuelve (ENT-16: se confirma al instante).

    registered_by es el operador en la tienda, donde se paga en efectivo (ENT-70); None si el cliente renta en línea.
    Siempre nace «Reservada»: si el cliente se la lleva al momento, el operador registra el recojo (ENT-91).
    """
    # Las reglas comparan horas de reloj (18:00, 09:00): se trabaja en hora local.
    start = timezone.localtime(start_datetime)
    end = timezone.localtime(end_datetime)
    # El periodo no necesita la base: se revisa antes de bloquear ninguna fila.
    check_period(start, end)
    with transaction.atomic():
        check_client_has_no_debt(client, registered_by)
        # Bloquea el equipo hasta el final: si dos confirman a la vez, el segundo ve la renta del primero (ENT-21).
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
    context = rental_context(rental, acting_username(rental.client, rental.registered_by))
    # «payment» y no «paid»: en línea nace pendiente y el PAYMENT_APPROVED de después no la contradice.
    log_event("RENTAL_CREATED", **context, payment="paid" if rental.is_paid else "pending")
    # En línea, el correo sale cuando el cliente presiona un botón del QR (payments.pay_with_qr).
    if rental.registered_by is None:
        return
    log_event("PAYMENT_CASH", **context)
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
    # Rental.Meta ordena por inicio: el primer choque es el más próximo y el mensaje nombra ese periodo.
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
    # Solo una renta que empieza después deja días libres antes; el equipo vuelve hasta las 09:00 de ese día.
    if busy_start > start:
        message += (
            f" Está libre hasta el {busy_start:%d/%m/%Y} a las {rules.LATEST_RETURN_TIME:%H:%M}."
        )
    return message
