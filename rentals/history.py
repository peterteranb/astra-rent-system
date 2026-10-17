"""Change the status of an equipment unit and keep its history (ENT-34)."""
from django.db import transaction

from .errors import InvalidStatusChangeError
from .models import Equipment, StatusChange
from .statuses import EquipmentStatus


def change_status(equipment, new_status, user, comment="") -> StatusChange:
    """Set the unit's new status and record who changed it, from what and why.

    This is the only place in the code that changes Equipment.status.
    Raises InvalidStatusChangeError if the unit is retired; then nothing changes.
    """
    with transaction.atomic():
        # Lock the row and read its current status, so two changes at the
        # same time cannot both start from the same old status.
        locked_equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        check_status_can_change(locked_equipment)
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


def check_status_can_change(equipment):
    """Raise InvalidStatusChangeError if the unit is retired."""
    if equipment.status == EquipmentStatus.RETIRED:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} está dado de baja; su estado ya no puede cambiar."
        )
