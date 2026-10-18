"""Use case PRE-CU-01: a client rents one unit for one period.

The view calls create_rental; this module applies the rules from
rules.py and talks to the database. It knows nothing about HTTP.
"""
from django.db import transaction
from django.utils import timezone

from . import rules
from .errors import EquipmentNotAvailableError, InvalidPeriodError, OutsideRentalHoursError
from .models import Equipment, EquipmentStatus, Rental

DATETIME_FORMAT = "%d/%m/%Y %H:%M"


def list_catalog():
    """Return the units shown in the catalog (PRE-CU-01, step 4)."""
    # ASSUMPTION: the catalog shows only "available" units. Whether it
    # should show all units is pending (Sesión 07 §7, PRE-02). Step 7
    # checks the unit again anyway, so this is only a convenience.
    return Equipment.objects.filter(status=EquipmentStatus.AVAILABLE)


def create_rental(
    client, equipment, start_datetime, end_datetime, registered_by=None, picked_up_at=None
) -> Rental:
    """Save a confirmed rental of one unit and return it (ENT-16).

    registered_by is the staff user who registered it (None when the
    client rents online); picked_up_at is set when the unit leaves now.
    Raises an OperationRejectedError subclass if a rule is broken; in that
    case nothing is saved and no rental or unit is changed.
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
        return Rental.objects.create(
            client=client,
            equipment=locked_equipment,
            start_datetime=start,
            end_datetime=end,
            registered_by=registered_by,
            picked_up_at=picked_up_at,
        )


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

    # Compare with every rental of this unit using the same rule the
    # unit tests check, instead of repeating the condition in SQL.
    now = timezone.now()

    for rental in equipment.rentals.all():
        # B2: Si la renta fue cancelada, no bloquea el equipo
        if rental.cancelled_at is not None:
            continue

        # B2: Si la renta ya fue devuelta, no bloquea el equipo
        if rental.returned_at is not None:
            continue

        # B2: Si pasó el tiempo límite de recojo y nunca se recogió, se considera expirada/no recogida y libera el equipo
        start_local = timezone.localtime(rental.start_datetime)
        if rental.picked_up_at is None and rules.is_pickup_expired(start_local, timezone.localtime(now)):
            continue

        # Validar solapamiento de fechas para las rentas que SÍ están vigentes/activas/pendientes
        if rules.periods_overlap(start, end, rental.start_datetime, rental.end_datetime):
            inicio_ocupado = timezone.localtime(rental.start_datetime).strftime(DATETIME_FORMAT)
            fin_ocupado = timezone.localtime(rental.end_datetime).strftime(DATETIME_FORMAT)

            raise EquipmentNotAvailableError(
                f"El equipo {equipment.inventory_id} está ocupado desde el "
                f"{inicio_ocupado} hasta el {fin_ocupado}. "
                f"Volverá a estar libre a partir del {fin_ocupado}."
            )

def cancel_rental(rental, cancelled_by) -> Rental:
    """Cancel a rental that has not yet been picked up."""
    if rental.picked_up_at is not None:
        raise ValueError("No se puede cancelar una reserva que ya ha sido recogida.")
    if rental.returned_at is not None:
        raise ValueError("No se puede cancelar una reserva que ya fue devuelta.")
    if rental.cancelled_at is not None:
        raise ValueError("La reserva ya se encuentra cancelada.")

    rental.cancelled_at = timezone.now()
    rental.cancelled_by = cancelled_by
    rental.save()
    return rental