"""Use case PRE-CU-01: a client rents one unit for one period.

The view calls create_rental; this module applies the rules from
rules.py and talks to the database. It knows nothing about HTTP.
"""
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

from . import rules
from .errors import (
    EquipmentNotAvailableError,
    InvalidPeriodError,
    OutsideRentalHoursError,
    RentalNotCancellableError,
)
from .models import Equipment, EquipmentStatus, Rental
from .roles import MAINTENANCE, OPERATOR
from .statuses import RentalStatus

DATETIME_FORMAT = "%d/%m/%Y %H:%M"

# #53: the catalog shows at most the next 3 busy periods of each unit.
MAX_BUSY_PERIODS_SHOWN = 3

# #50: the operator picks the client from a short list, not from every client.
MAX_CLIENTS_FOUND = 10


@dataclass(frozen=True)
class CatalogEntry:
    """One unit of the catalog with the rentals that keep it busy from now on."""

    equipment: Equipment
    busy_rentals: list[Rental]


def list_catalog():
    """Return the units shown in the catalog (PRE-CU-01, step 4)."""
    # ASSUMPTION: the catalog shows only "available" units, each with the
    # dates it is busy, so the client sees what can be rented and until
    # when (ENT-61, ENT-64). Whether it should also show the units in review
    # or repair is pending (Sesión 07 §7, PRE-02). Step 7 checks the unit
    # again anyway, so this is only a convenience.
    return Equipment.objects.filter(status=EquipmentStatus.AVAILABLE)


def catalog_entries(now) -> list[CatalogEntry]:
    """Return each catalog unit with its next busy periods at now, soonest first (#53)."""
    # One extra query for all the units instead of one per unit. Only rentals
    # that have not ended can be busy from now on; the prefetch keeps
    # Rental.Meta's order by start.
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
    """Return the first rentals that still hold the unit at now, up to MAX_BUSY_PERIODS_SHOWN."""
    # Expiry depends on the La Paz clock, so the model rule decides it
    # instead of repeating the pickup deadline in SQL.
    busy = [rental for rental in rentals if rental.occupies_equipment_at(now)]
    return busy[:MAX_BUSY_PERIODS_SHOWN]


def client_accounts():
    """Return the users who are clients: not staff, not superusers and not in a staff role."""
    return (
        get_user_model()
        .objects.filter(is_staff=False, is_superuser=False)
        .exclude(groups__name__in=[OPERATOR, MAINTENANCE])
    )


def find_clients(text):
    """Return up to MAX_CLIENTS_FOUND clients whose username, names or email contain text (ENT-54)."""
    text = text.strip()
    # An empty search would list every client; the operator must type something.
    if not text:
        return client_accounts().none()
    matches = (
        Q(username__icontains=text)
        | Q(first_name__icontains=text)
        | Q(last_name__icontains=text)
        | Q(email__icontains=text)
    )
    return client_accounts().filter(matches).order_by("username")[:MAX_CLIENTS_FOUND]


def create_rental(
    client, equipment, start_datetime, end_datetime, registered_by=None, picked_up_now=False
) -> Rental:
    """Save a confirmed rental of one unit and return it (ENT-16).

    registered_by is the staff user who registered it (None when the
    client rents online). picked_up_now means the client takes the unit
    at the store right away: the rental is born "rented", handed over by
    registered_by (ENT-57). Raises an OperationRejectedError subclass if a
    rule is broken; in that case nothing is saved and no rental or unit is changed.
    """
    # The rules compare clock times (18:00, 09:00), so work in local time.
    start = timezone.localtime(start_datetime)
    end = timezone.localtime(end_datetime)

    # Period rules do not need the database, so check them first.
    check_period(start, end)

    with transaction.atomic():
        # Lock the unit's row until the transaction ends. If two clients
        # confirm at the same time, the second one waits here and then
        # sees the first rental, so the first click wins (ENT-21).
        # Reading the row again also gets its current status.
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
            # No client rule yet for taking a unit now with a later start; pending question (ENT-57).
            rental.picked_up_at = timezone.now()
            rental.handed_over_by = registered_by
        rental.save()
        return rental


def check_period(start, end):
    """Raise if the period itself breaks a rule, whatever the unit."""
    if not rules.ends_after_start(start, end):
        raise InvalidPeriodError(
            "La fecha y hora de devolución debe ser posterior a la de recojo."
        )
    if not rules.is_within_max_duration(start, end):
        raise InvalidPeriodError(
            f"La renta no puede durar más de {rules.MAX_RENTAL_DURATION.days} días."
        )
    if not rules.is_pickup_time_allowed(start):
        raise OutsideRentalHoursError(
            f"El recojo debe ser desde las {rules.EARLIEST_PICKUP_TIME:%H:%M}."
        )
    if not rules.is_return_time_allowed(end):
        raise OutsideRentalHoursError(
            f"La devolución debe ser hasta las {rules.LATEST_RETURN_TIME:%H:%M}."
        )


def check_equipment_is_free(equipment, start, end):
    """Raise EquipmentNotAvailableError if the unit cannot be rented then (E1)."""
    if not rules.is_rentable_status(equipment.status):
        raise EquipmentNotAvailableError(
            f"El equipo {equipment.inventory_id} no está disponible "
            f"(estado: {equipment.get_status_display()})."
        )

    # Compare with every rental of this unit using the same rules the
    # unit tests check, instead of repeating the conditions in SQL.
    # Rentals come ordered by start (Rental.Meta), so the first clash is the
    # one that starts first and the message names the closest busy period.
    now = timezone.now()
    for rental in equipment.rentals.all():
        if not rental.occupies_equipment_at(now):
            continue
        if rules.periods_overlap(start, end, rental.start_datetime, rental.end_datetime):
            raise EquipmentNotAvailableError(busy_message(equipment, rental, start))


def busy_message(equipment, rental, start):
    """Say when the unit is busy and, if that rental starts later, until when it is free (ENT-36, ENT-64)."""
    busy_start = timezone.localtime(rental.start_datetime)
    busy_end = timezone.localtime(rental.end_datetime)
    message = (
        f"El equipo {equipment.inventory_id} está ocupado "
        f"del {busy_start:{DATETIME_FORMAT}} al {busy_end:{DATETIME_FORMAT}}."
    )
    # Only a rental that starts after the requested pickup leaves free days
    # before it, and the unit must be back by 09:00 of its first day (#47).
    if busy_start > start:
        message += (
            f" Está libre hasta el {busy_start:%d/%m/%Y} a las {rules.LATEST_RETURN_TIME:%H:%M}."
        )
    return message


def cancel_rental(rental, cancelled_by) -> Rental:
    """Cancel a reservation not picked up yet and record who cancelled it (ENT-55).

    Its dates are free for others at once, because a cancelled rental no
    longer occupies the unit. Raises RentalNotCancellableError if the rental
    is not "reserved"; then nothing changes.
    """
    with transaction.atomic():
        # Lock the rental's row and read it again, so a pickup and a
        # cancellation clicked at the same time cannot both be saved.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_cancel(locked_rental, now)
        locked_rental.cancelled_at = now
        locked_rental.cancelled_by = cancelled_by
        locked_rental.save(update_fields=["cancelled_at", "cancelled_by"])
        return locked_rental


def check_can_cancel(rental, now):
    """Raise RentalNotCancellableError unless the rental is "reserved" at now (#49)."""
    status = rental.status_at(now)
    if status == RentalStatus.RESERVED:
        return
    raise RentalNotCancellableError(not_cancellable_message(rental, status))


def not_cancellable_message(rental, status):
    """Say why the rental is no longer a reservation, with the moment it stopped being one."""
    inventory_id = rental.equipment.inventory_id
    if status == RentalStatus.CANCELLED:
        return f"La renta de {inventory_id} ya fue cancelada el {local_text(rental.cancelled_at)}."
    if status == RentalStatus.RETURNED:
        return f"La renta de {inventory_id} ya fue devuelta el {local_text(rental.returned_at)}."
    if status == RentalStatus.RENTED:
        return f"La renta de {inventory_id} ya fue entregada el {local_text(rental.picked_up_at)}."
    return f"La reserva de {inventory_id} venció a las {rules.PICKUP_DEADLINE:%H:%M}."


def local_text(moment):
    """Write a moment as La Paz date and time, the way the messages show it."""
    return f"{timezone.localtime(moment):{DATETIME_FORMAT}}"