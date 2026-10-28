"""Caso de uso CU-13, y un paso de CU-09 y CU-10: cambia el estado de un equipo, guarda su historial (ENT-34) y, si sale de servicio, cancela sus reservas."""
from django.db import transaction

from ..errors import InvalidStatusChangeError
from ..models import Equipment, Rental, StatusChange
from ..services.events import log_event, logs_rejection
from ..statuses import EquipmentStatus
from .renting import cancel_reservations

# ENT-88: un equipo que pasa a reparación o baja cancela sus reservas todavía no recogidas.
OUT_OF_SERVICE_REASONS = {
    EquipmentStatus.IN_REPAIR: "El equipo no está disponible: pasó a reparación.",
    EquipmentStatus.RETIRED: "El equipo no está disponible: se dio de baja.",
}


@logs_rejection("STATUS_CHANGE_REJECTED")
def change_status(equipment, new_status, user, comment="") -> StatusChange:
    """Pone el estado nuevo del equipo y guarda quién lo cambió, desde cuál y por qué.

    Es el único lugar del código que cambia Equipment.status.
    Lanza InvalidStatusChangeError si el cambio no se permite; entonces nada cambia.
    """
    with transaction.atomic():
        # Bloquea la fila y lee el estado actual: dos cambios a la vez
        # no pueden partir del mismo estado anterior.
        locked_equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        check_status_can_change(locked_equipment, new_status)
        change = StatusChange(
            equipment=locked_equipment,
            old_status=locked_equipment.status,
            new_status=new_status,
            changed_by=user,
            comment=comment,
        )
        locked_equipment.status = new_status
        locked_equipment.save(update_fields=["status"])
        change.save()
    log_event(
        "STATUS_CHANGED",
        equipment=locked_equipment.inventory_id,
        old=change.old_status,
        new=new_status,
        by=user.username,
    )
    return change


def check_status_can_change(equipment, new_status):
    """Lanza InvalidStatusChangeError si el equipo está de baja o ya tiene new_status."""
    # ENT-49: la baja es definitiva.
    if equipment.status == EquipmentStatus.RETIRED:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} está dado de baja; su estado ya no puede cambiar."
        )
    # Un cambio al mismo estado dejaría en el historial una fila sin cambio real.
    if equipment.status == new_status:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} ya está «{equipment.get_status_display()}»."
        )


def correct_status(equipment, new_status, user) -> StatusChange:
    """El admin corrige el estado de un equipo (CU-13); si sale de servicio cancela sus reservas, pero nunca cobra (ENT-75)."""
    # Una sola transacción: el estado y las cancelaciones se guardan juntos o nada.
    with transaction.atomic():
        change = change_status(equipment, new_status, user)
        cancel_if_out_of_service(change.equipment, new_status, user)
    return change


def cancel_if_out_of_service(equipment, new_status, user) -> list[Rental]:
    """Cancela las reservas no recogidas del equipo si new_status lo saca de servicio y las devuelve (ENT-88)."""
    reason = OUT_OF_SERVICE_REASONS.get(new_status)
    if reason is None:
        return []
    return cancel_reservations(Rental.objects.filter(equipment=equipment), user, reason)
