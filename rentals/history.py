"""Cambia el estado de un equipo y guarda su historial (ENT-34: cada cambio queda con quién, cuándo y por qué)."""
from django.db import transaction

from .errors import InvalidStatusChangeError
from .models import Equipment, StatusChange
from .statuses import EquipmentStatus


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
