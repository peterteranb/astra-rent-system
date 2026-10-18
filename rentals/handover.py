"""Use case: the operator hands a reserved unit over to the client and receives it back."""
from django.db import transaction
from django.utils import timezone

from . import rules
from .errors import AlreadyPickedUpError, RentalCancelledError, ReservationExpiredError
from .models import Rental
from .renting import DATETIME_FORMAT
from .statuses import RentalStatus


def reservations_to_hand_over() -> list[Rental]:
    """Return the "reserved" rentals the operator can still hand over, soonest first (C2)."""
    pending = (
        Rental.objects.filter(
            picked_up_at__isnull=True, cancelled_at__isnull=True, returned_at__isnull=True
        )
        .select_related("equipment", "client")
        .order_by("start_datetime")
    )
    # The database drops what is clearly not reserved; expiry depends on the
    # clock time in La Paz, so status_at() decides it with the same rule
    # used everywhere else instead of repeating the deadline in SQL.
    now = timezone.now()
    return [rental for rental in pending if rental.status_at(now) == RentalStatus.RESERVED]


def register_pickup(rental, staff_user) -> Rental:
    """Record that the client took the unit now and which operator handed it over (C1).

    Only the rental changes: "rented" is calculated from picked_up_at,
    so Equipment.status is not touched. Raises an OperationRejectedError
    subclass if the rental cannot be handed over; then nothing changes.
    """
    with transaction.atomic():
        # Lock the rental's row and read it again. If two operators click at
        # the same time, the second one waits here and then sees picked_up_at
        # already set, so the pickup is registered only once.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_pick_up(locked_rental, now)
        locked_rental.picked_up_at = now
        locked_rental.handed_over_by = staff_user
        locked_rental.save(update_fields=["picked_up_at", "handed_over_by"])
        return locked_rental


def check_can_pick_up(rental, now):
    """Raise if the rental is cancelled, already picked up or expired at now."""
    # Same order as Rental.status_at(): a cancellation is final, and a
    # rental already picked up can no longer expire, so expiry goes last.
    inventory_id = rental.equipment.inventory_id
    if rental.cancelled_at is not None:
        raise RentalCancelledError(f"La renta de {inventory_id} fue cancelada.")
    if rental.picked_up_at is not None:
        picked_up_at = timezone.localtime(rental.picked_up_at)
        raise AlreadyPickedUpError(
            f"La renta de {inventory_id} ya fue entregada el {picked_up_at:{DATETIME_FORMAT}}."
        )
    # status_at() already applies rules.is_pickup_expired; reuse it instead
    # of repeating the deadline here.
    if rental.status_at(now) == RentalStatus.NOT_PICKED_UP:
        raise ReservationExpiredError(
            f"La reserva de {inventory_id} venció a las {rules.PICKUP_DEADLINE:%H:%M}."
        )


def register_return(rental, staff_user, note):
    """Record that the client returned the unit of the rental."""
    raise NotImplementedError
