"""Casos de uso CU-03 y CU-04: el operador entrega un equipo reservado y lo recibe de vuelta."""
from django.db import transaction
from django.utils import timezone

from . import history
from .errors import IncompleteReturnError, RentalStateError
from .formatting import rental_state_message
from .models import Rental
from .statuses import EquipmentStatus, RentalStatus


def reservations_to_hand_over() -> list[Rental]:
    """Devuelve las rentas «Reservadas» que el operador todavía puede entregar, la más próxima primero."""
    pending = (
        Rental.objects.filter(
            picked_up_at__isnull=True, cancelled_at__isnull=True, returned_at__isnull=True
        )
        .select_related("equipment", "client")
        .order_by("start_datetime")
    )
    # El vencimiento depende de la hora de La Paz, así que lo decide status_at()
    # con la misma regla de todo el sistema en vez de repetirla en SQL.
    now = timezone.now()
    return [rental for rental in pending if rental.status_at(now) == RentalStatus.RESERVED]


def rentals_to_receive():
    """Devuelve las rentas ni devueltas ni canceladas, la que vence primero arriba.

    Incluye las que nunca se recogieron (ENT-60: el sistema deja devolverlas).
    """
    return (
        Rental.objects.filter(returned_at__isnull=True, cancelled_at__isnull=True)
        .select_related("equipment", "client")
        .order_by("end_datetime")
    )


def register_pickup(rental, staff_user) -> Rental:
    """Guarda que el cliente se llevó el equipo ahora y qué operador lo entregó (RF-08).

    Solo cambia la renta: «Rentada» se calcula desde picked_up_at, así que
    Equipment.status no se toca. Lanza RentalStateError si no está «Reservada».
    """
    with transaction.atomic():
        # Bloquea la fila y la vuelve a leer: si dos operadores hacen clic a la
        # vez, el segundo espera aquí y ve el recojo del primero.
        locked_rental = Rental.objects.select_for_update().get(pk=rental.pk)
        now = timezone.now()
        check_can_pick_up(locked_rental, now)
        locked_rental.picked_up_at = now
        locked_rental.handed_over_by = staff_user
        locked_rental.save(update_fields=["picked_up_at", "handed_over_by"])
        return locked_rental


def check_can_pick_up(rental, now):
    """Lanza RentalStateError si en now la renta no está «Reservada»."""
    status = rental.status_at(now)
    if status != RentalStatus.RESERVED:
        raise RentalStateError(rental_state_message(rental, status))


def register_return(rental, staff_user, note) -> Rental:
    """Guarda que el equipo volvió ahora y cómo llegó, y lo manda a revisión (RF-04, RF-08).

    Lanza IncompleteReturnError sin observación y RentalStateError si la renta
    está cancelada o ya devuelta; entonces nada cambia.
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
        return locked_rental


def check_can_return(rental):
    """Lanza RentalStateError si la renta está cancelada o ya devuelta."""
    status = rental.status
    if status in (RentalStatus.CANCELLED, RentalStatus.RETURNED):
        raise RentalStateError(rental_state_message(rental, status))
