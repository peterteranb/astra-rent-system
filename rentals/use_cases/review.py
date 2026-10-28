"""Caso de uso CU-10: mantenimiento revisa un equipo devuelto, decide su estado nuevo y cobra el daño."""
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .. import rules
from ..errors import InvalidStatusChangeError
from ..models import Debt, Equipment, Rental, StatusChange
from ..services.events import logs_rejection
from ..statuses import DebtReason, EquipmentStatus
from .history import change_status
from .payments import charge_debt
from .renting import cancel_rental

# ENT-49: desde revisión o reparación un equipo pasa a disponible, a
# reparación o a baja, y la baja es definitiva.
REVIEW_RESULTS = (
    EquipmentStatus.AVAILABLE,
    EquipmentStatus.IN_REPAIR,
    EquipmentStatus.RETIRED,
)


@dataclass(frozen=True)
class ReviewOutcome:
    """Lo que dejó una revisión: el cambio de estado, la deuda (si hubo) y las reservas canceladas."""

    change: StatusChange
    debt: Debt | None
    cancelled: list[Rental]


def equipment_to_review():
    """Devuelve los equipos que esperan a mantenimiento: en revisión o en reparación."""
    return Equipment.objects.filter(
        status__in=[EquipmentStatus.IN_REVIEW, EquipmentStatus.IN_REPAIR]
    )


def review_queue():
    """Devuelve los equipos que esperan a mantenimiento, cada uno con las opciones que puede elegir (CU-10)."""
    return [(equipment, review_choices_for(equipment)) for equipment in equipment_to_review()]


def review_choices_for(equipment):
    """Devuelve las opciones (valor, etiqueta) del formulario de revisión, sin el estado actual."""
    return [
        (status.value, status.label) for status in REVIEW_RESULTS if status != equipment.status
    ]


@logs_rejection("REVIEW_REJECTED")
def review_equipment(equipment, staff_user, new_status, comment="") -> ReviewOutcome:
    """Guarda el estado nuevo de un equipo revisado con su historial, su deuda y sus cancelaciones.

    Reparación o baja cobran al cliente de la última renta devuelta; la baja además
    cancela las reservas futuras del equipo (ENT-74). Lanza InvalidStatusChangeError
    si new_status no es un resultado de revisión o el equipo no puede cambiar.
    """
    check_review_result(equipment, new_status)
    # Una sola transacción: el estado, la deuda y las cancelaciones se guardan juntos o nada.
    with transaction.atomic():
        change = change_status(equipment, new_status, staff_user, comment.strip())
        debt = charge_damage(change.equipment, new_status)
        cancelled = []
        if new_status == EquipmentStatus.RETIRED:
            cancelled = cancel_future_reservations(change.equipment, staff_user)
    return ReviewOutcome(change, debt, cancelled)


def check_review_result(equipment, new_status):
    """Lanza InvalidStatusChangeError si new_status no es disponible, en reparación o baja."""
    if new_status not in REVIEW_RESULTS:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} solo puede pasar a disponible, en reparación o baja."
        )


def charge_damage(equipment, new_status):
    """Cobra la reparación o la baja al cliente de la última renta devuelta; None si no hay a quién o qué cobrar."""
    rental = last_returned_rental(equipment)
    if rental is None:
        return None
    charge = rules.damage_charge(equipment.value, new_status, damage_charged_on(rental))
    if charge is None:
        return None
    reason, amount = charge
    return charge_debt(rental, reason, amount)


def damage_charged_on(rental) -> Decimal:
    """Devuelve lo que la renta ya debe o pagó por daño: sus deudas de reparación y de baja."""
    return rental.debts.filter(reason__in=[DebtReason.REPAIR, DebtReason.RETIRED]).total()


def last_returned_rental(equipment):
    """Devuelve la última renta devuelta del equipo, o None si nunca volvió de una renta."""
    return equipment.rentals.filter(returned_at__isnull=False).order_by("-returned_at").first()


def cancel_future_reservations(equipment, staff_user):
    """Cancela las reservas todavía no recogidas de un equipo dado de baja y las devuelve (ENT-74)."""
    reservations = Rental.objects.reserved_at(timezone.now()).filter(equipment=equipment)
    reason = "El equipo se dio de baja en la revisión."
    return [cancel_rental(reservation, staff_user, reason) for reservation in reservations]
