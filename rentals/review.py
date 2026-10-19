"""Caso de uso CU-05: mantenimiento revisa un equipo devuelto y decide su estado nuevo."""
from .errors import InvalidStatusChangeError
from .history import change_status
from .models import Equipment
from .statuses import EquipmentStatus

# ENT-49: desde revisión o reparación un equipo pasa a disponible, a
# reparación o a baja, y la baja es definitiva.
REVIEW_RESULTS = (
    EquipmentStatus.AVAILABLE,
    EquipmentStatus.IN_REPAIR,
    EquipmentStatus.RETIRED,
)


def equipment_to_review():
    """Devuelve los equipos que esperan a mantenimiento: en revisión o en reparación."""
    return Equipment.objects.filter(
        status__in=[EquipmentStatus.IN_REVIEW, EquipmentStatus.IN_REPAIR]
    )


def review_choices_for(equipment):
    """Devuelve las opciones (valor, etiqueta) del formulario de revisión, sin el estado actual."""
    return [
        (status.value, status.label) for status in REVIEW_RESULTS if status != equipment.status
    ]


def review_equipment(equipment, staff_user, new_status, comment=""):
    """Guarda el estado nuevo de un equipo revisado con su fila de historial y la devuelve.

    Lanza InvalidStatusChangeError si new_status no es un resultado de revisión
    o el equipo no puede cambiar; entonces nada cambia.
    """
    check_review_result(equipment, new_status)
    return change_status(equipment, new_status, staff_user, comment.strip())


def check_review_result(equipment, new_status):
    """Lanza InvalidStatusChangeError si new_status no es disponible, en reparación o baja."""
    if new_status not in REVIEW_RESULTS:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} solo puede pasar a disponible, en reparación o baja."
        )
