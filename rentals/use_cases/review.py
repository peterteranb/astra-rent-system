"""Caso de uso CU-10: mantenimiento revisa cualquier equipo, decide su estado nuevo y si cobra el daño (ENT-90)."""
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import Case, IntegerField, Prefetch, Value, When

from .. import rules
from ..errors import InvalidStatusChangeError
from ..models import Debt, Equipment, Rental, StatusChange
from ..services.events import log_event, logs_rejection
from ..services.formatting import charge_label
from ..statuses import DebtReason, EquipmentStatus
from .history import cancel_if_out_of_service, change_status
from .payments import charge_debt


@dataclass(frozen=True)
class ReviewEntry:
    """Un equipo de la lista de mantenimiento: sus opciones y su última renta devuelta, si tiene."""

    equipment: Equipment
    choices: list
    last_rental: Rental | None

    @property
    def charge_label(self):
        """Texto de la casilla para cobrar el daño, o vacío si no hay a quién cobrar."""
        return charge_label(self.last_rental) if self.last_rental else ""


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


def review_queue(status=""):
    """Devuelve los equipos que no están de baja, con el filtro de estado; los que esperan revisión van primero (CU-10)."""
    equipment = reviewable_equipment()
    if status:
        equipment = equipment.filter(status=status)
    return [
        ReviewEntry(unit, review_choices_for(unit), next(iter(unit.returned_rentals), None))
        for unit in equipment
    ]


def reviewable_equipment():
    """Equipos que no están de baja, primero los «En revisión», cada uno con sus rentas devueltas, la última primero."""
    # Una sola consulta trae las rentas de todos los equipos, no una por equipo.
    returned = Prefetch(
        "rentals",
        queryset=Rental.objects.filter(returned_at__isnull=False).select_related("client").order_by("-returned_at"),
        to_attr="returned_rentals",
    )
    waits_review = Case(
        When(status=EquipmentStatus.IN_REVIEW, then=Value(0)), default=Value(1), output_field=IntegerField()
    )
    return (
        Equipment.objects.exclude(status=EquipmentStatus.RETIRED)
        .order_by(waits_review, "inventory_id")
        .prefetch_related(returned)
    )


def review_choices_for(equipment):
    """Devuelve las opciones (valor, etiqueta) del formulario: los estados permitidos desde el actual."""
    return [(status.value, status.label) for status in rules.next_statuses(equipment.status)]


@logs_rejection("REVIEW_REJECTED")
def review_equipment(equipment, staff_user, new_status, comment="", charge_last_client=False) -> ReviewOutcome:
    """Guarda el estado nuevo de un equipo revisado con su historial, su deuda y sus cancelaciones.

    Reparación o baja cancelan las reservas no recogidas (ENT-88) y, solo con charge_last_client,
    cobran al cliente de la última renta devuelta (ENT-74, ENT-90). Lanza InvalidStatusChangeError
    si new_status no es un estado del equipo o el equipo no puede cambiar.
    """
    check_review_result(equipment, new_status)
    # Una sola transacción: el estado, la deuda y las cancelaciones se guardan juntos o nada.
    with transaction.atomic():
        change = change_status(equipment, new_status, staff_user, comment.strip())
        debt = settle_damage(change.equipment, new_status, staff_user, charge_last_client)
        cancelled = cancel_if_out_of_service(change.equipment, new_status, staff_user)
    return ReviewOutcome(change, debt, cancelled)


def check_review_result(equipment, new_status):
    """Lanza InvalidStatusChangeError si new_status no es un estado del equipo."""
    if new_status not in EquipmentStatus.values:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} solo puede pasar a disponible, en revisión, en reparación o baja."
        )


def settle_damage(equipment, new_status, staff_user, charge_last_client):
    """Cobra el daño si mantenimiento lo pidió; si no lo pidió y había a quién cobrar, escribe DAMAGE_NOT_CHARGED (ENT-90)."""
    if rules.damage_reason_and_rate(new_status) is None:
        return None
    rental = last_returned_rental(equipment)
    if rental is None:
        return None
    if not charge_last_client:
        log_event(
            "DAMAGE_NOT_CHARGED",
            equipment=equipment.inventory_id,
            rental=rental.pk,
            client=rental.client.username,
            status=new_status,
            by=staff_user.username,
        )
        return None
    return charge_damage(rental, equipment, new_status)


def charge_damage(rental, equipment, new_status):
    """Cobra la reparación o la baja al cliente de la renta; None si ya no queda nada que cobrar (D-06)."""
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
