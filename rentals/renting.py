"""Casos de uso CU-01, CU-02 y CU-06: catálogo, renta en línea y en tienda, y cancelar una reserva.

Las vistas llaman a este módulo; aplica las reglas de rules.py y habla con la base. No lee la petición ni elige páginas.
"""
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from . import rules
from .errors import EquipmentNotAvailableError, InvalidPeriodError, RentalStateError
from .formatting import local_text, rental_state_message
from .models import Equipment, EquipmentStatus, Rental
from .roles import CLIENT
from .statuses import RentalStatus

# ENT-64: el catálogo dice cuándo está ocupado cada equipo; con 3 periodos basta para elegir fechas.
MAX_BUSY_PERIODS_SHOWN = 3

# RF-06: el operador elige al cliente de una lista corta, no de todos los clientes.
MAX_CLIENTS_FOUND = 10


@dataclass(frozen=True)
class CatalogEntry:
    """Un equipo del catálogo con las rentas que lo ocupan desde ahora."""

    equipment: Equipment
    busy_rentals: list[Rental]


def list_catalog():
    """Devuelve los equipos que muestra el catálogo: solo los «Disponibles».

    ENT-61 y ENT-64: un equipo con rentas futuras sigue disponible y el
    catálogo dice cuándo está ocupado. create_rental vuelve a revisar el equipo.
    """
    return Equipment.objects.filter(status=EquipmentStatus.AVAILABLE)


def catalog_entries(now) -> list[CatalogEntry]:
    """Devuelve cada equipo del catálogo con sus próximos periodos ocupados en now, el más próximo primero."""
    # Una sola consulta extra para todos los equipos en vez de una por equipo.
    # Solo las rentas que no terminaron pueden ocupar el equipo desde ahora.
    upcoming = Prefetch(
        "rentals",
        queryset=Rental.objects.filter(end_datetime__gt=now),
        to_attr="upcoming_rentals",
    )
    return [
        CatalogEntry(equipment, busy_rentals_at(equipment.upcoming_rentals, now))
        for equipment in list_catalog().prefetch_related(upcoming)
    ]


def busy_rentals_at(rentals, now) -> list[Rental]:
    """Devuelve las primeras rentas que todavía ocupan el equipo en now, hasta MAX_BUSY_PERIODS_SHOWN."""
    busy = [rental for rental in rentals if rental.occupies_equipment_at(now)]
    return busy[:MAX_BUSY_PERIODS_SHOWN]


def client_accounts():
    """Devuelve los usuarios con el rol cliente."""
    return get_user_model().objects.filter(role__code=CLIENT)


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
    """Devuelve las rentas del cliente, la más reciente primero (HU-08)."""
    return Rental.objects.filter(client=client).select_related("equipment").order_by("-start_datetime")


def visible_rental(user, rental_id) -> Rental:
    """Devuelve la renta si user es su cliente o quien la registró; si no, responde 404."""
    # Filtrar por usuario hace que nadie más pueda abrir la renta, ni saber que existe.
    return get_object_or_404(Rental, Q(client=user) | Q(registered_by=user), pk=rental_id)


def create_rental(
    client, equipment, start_datetime, end_datetime, registered_by=None, picked_up_now=False
) -> Rental:
    """Guarda una renta confirmada de un equipo y la devuelve (ENT-16: se confirma al instante).

    registered_by es el operador que la registró (None si el cliente renta en
    línea). Con picked_up_now el cliente se lo lleva en la tienda: la renta nace
    «Rentada» (ENT-57). Lanza un OperationRejectedError si se rompe una regla;
    entonces no se guarda nada.
    """
    # Las reglas comparan horas de reloj (18:00, 09:00): se trabaja en hora local.
    start = timezone.localtime(start_datetime)
    end = timezone.localtime(end_datetime)
    # El periodo no necesita la base: se revisa antes de bloquear ninguna fila.
    check_period(start, end)
    with transaction.atomic():
        # Bloquea la fila del equipo hasta el final: si dos clientes confirman a la
        # vez, el segundo espera aquí y ve la renta del primero (ENT-21: gana el primer clic).
        locked_equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        check_equipment_is_free(locked_equipment, start, end)
        rental = Rental(
            client=client,
            equipment=locked_equipment,
            start_datetime=start,
            end_datetime=end,
            registered_by=registered_by,
        )
        if picked_up_now:
            # Pendiente con el cliente: qué pasa si se lo lleva ahora y el periodo empieza después (ENT-57).
            rental.picked_up_at = timezone.now()
            rental.handed_over_by = registered_by
        rental.save()
        return rental


def check_period(start, end):
    """Lanza InvalidPeriodError si el periodo mismo rompe una regla, sea cual sea el equipo."""
    if not rules.ends_after_start(start, end):
        raise InvalidPeriodError(
            "La fecha y hora de devolución debe ser posterior a la de recojo."
        )
    if not rules.is_within_max_duration(start, end):
        raise InvalidPeriodError(
            f"La renta no puede durar más de {rules.MAX_RENTAL_DURATION.days} días."
        )
    if not rules.is_pickup_time_allowed(start):
        raise InvalidPeriodError(
            f"El recojo debe ser desde las {rules.EARLIEST_PICKUP_TIME:%H:%M}."
        )
    if not rules.is_return_time_allowed(end):
        raise InvalidPeriodError(
            f"La devolución debe ser hasta las {rules.LATEST_RETURN_TIME:%H:%M}."
        )


def check_equipment_is_free(equipment, start, end):
    """Lanza EquipmentNotAvailableError si el equipo no se puede rentar en ese periodo (RF-01)."""
    if not rules.is_rentable_status(equipment.status):
        raise EquipmentNotAvailableError(
            f"El equipo {equipment.inventory_id} no está disponible "
            f"(estado: {equipment.get_status_display()})."
        )
    # Las rentas vienen ordenadas por inicio (Rental.Meta): el primer choque es el
    # más próximo, y el mensaje nombra ese periodo.
    now = timezone.now()
    for rental in equipment.rentals.all():
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


def cancel_rental(rental, cancelled_by) -> Rental:
    """Cancela una reserva todavía no recogida y guarda quién la canceló (ENT-55).

    Sus fechas quedan libres al instante, porque una renta cancelada ya no
    ocupa el equipo. Lanza RentalStateError si no está «Reservada».
    """
    with transaction.atomic():
        # Bloquea la fila: un recojo y una cancelación a la vez no se guardan los dos.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_cancel(locked_rental, now)
        locked_rental.cancelled_at = now
        locked_rental.cancelled_by = cancelled_by
        locked_rental.save(update_fields=["cancelled_at", "cancelled_by"])
        return locked_rental


def check_can_cancel(rental, now):
    """Lanza RentalStateError si en now la renta no está «Reservada» (HU-06)."""
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))
