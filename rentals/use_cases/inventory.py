"""Caso de uso CU-12: el administrador registra un equipo nuevo, a mano (ENT-83)."""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from ..errors import EquipmentRegistrationError
from ..models import Equipment
from ..services.events import equipment_text, log_event, logs_rejection, named

REJECTION_TITLE = "No se registró el equipo:"


def normalize_inventory_id(text):
    """Quita los espacios y pasa el código a mayúsculas: «mes-00021» se guarda «MES-00021»."""
    return text.strip().upper()


def attempted_equipment(inventory_id, serial_number, name, value, registered_by):
    """Los datos del equipo que se intentó registrar, para el log del rechazo."""
    return {
        "equipment": named(normalize_inventory_id(inventory_id), name.strip()),
        "serial": serial_number.strip(),
        "value": "-" if value is None else value,
        "by": registered_by.username,
    }


@logs_rejection("EQUIPMENT_REJECTED", attempted_equipment)
def register_equipment(inventory_id, serial_number, name, value, registered_by) -> Equipment:
    """Guarda un equipo nuevo «Disponible» y lo devuelve (ENT-83).

    Usa las mismas reglas del modelo que el admin de Django; si algo falla, lanza
    EquipmentRegistrationError con todas las causas juntas y no guarda nada.
    """
    equipment = Equipment(
        inventory_id=normalize_inventory_id(inventory_id),
        serial_number=serial_number.strip(),
        name=name.strip(),
        value=value,
    )
    check_new_equipment(equipment)
    # Sin fila que bloquear: si dos admins guardan el mismo código, el índice único rechaza al segundo.
    try:
        with transaction.atomic():
            equipment.save()
    except IntegrityError as error:
        raise EquipmentRegistrationError(
            REJECTION_TITLE, ["Ya existe un equipo con este código o número de serie."]
        ) from error
    log_equipment_registered(equipment, registered_by)
    return equipment


def log_equipment_registered(equipment, registered_by):
    """Escribe EQUIPMENT_REGISTERED; lo usan esta página y el admin de Django."""
    log_event(
        "EQUIPMENT_REGISTERED",
        equipment=equipment_text(equipment),
        serial=equipment.serial_number,
        value=equipment.value,
        by=registered_by.username,
    )


def check_new_equipment(equipment):
    """Lanza EquipmentRegistrationError con todas las causas si el equipo rompe una regla del modelo."""
    try:
        equipment.full_clean()
    except ValidationError as error:
        raise EquipmentRegistrationError(REJECTION_TITLE, error.messages) from error
