"""Caso de uso CU-12: el administrador registra un equipo nuevo, a mano (ENT-83)."""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .errors import EquipmentRegistrationError
from .models import Equipment

REJECTION_TITLE = "No se registró el equipo:"


def normalize_inventory_id(text):
    """Quita los espacios y pasa el código a mayúsculas: «mes-00021» se guarda «MES-00021»."""
    return text.strip().upper()


def register_equipment(inventory_id, serial_number, name, value) -> Equipment:
    """Guarda un equipo nuevo «Disponible» y lo devuelve.

    Usa las mismas reglas del modelo que el admin de Django: formato del código,
    código y serie únicos, nombre y valor mayor que 0. Si algo falla, lanza
    EquipmentRegistrationError con todas las causas y no guarda nada.
    """
    equipment = Equipment(
        inventory_id=normalize_inventory_id(inventory_id),
        serial_number=serial_number.strip(),
        name=name.strip(),
        value=value,
    )
    check_new_equipment(equipment)
    # No hay fila que bloquear: si dos admins guardan el mismo código a la vez,
    # los índices únicos de la base rechazan al segundo.
    try:
        with transaction.atomic():
            equipment.save()
    except IntegrityError as error:
        raise EquipmentRegistrationError(
            REJECTION_TITLE, ["Ya existe un equipo con este código o número de serie."]
        ) from error
    return equipment


def check_new_equipment(equipment):
    """Lanza EquipmentRegistrationError con todas las causas si el equipo rompe una regla del modelo."""
    try:
        equipment.full_clean()
    except ValidationError as error:
        raise EquipmentRegistrationError(REJECTION_TITLE, error.messages) from error
