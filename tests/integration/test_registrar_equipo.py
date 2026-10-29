"""Prueba rentals/use_cases/inventory.py con la base: register_equipment(), alta de equipos y restricciones de códigos duplicados."""
import pytest
from django.core.exceptions import ValidationError

from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from rentals.use_cases.inventory import register_equipment
from tests.helpers import foto_de_la_base


def test_alta_de_equipos_en_inventario_y_validacion_de_duplicados(mt01):
    # Registrar equipo con datos válidos lo crea en estado disponible; duplicar el código de inventario o serie rechaza con error
    # Comprueba que el personal autorizado registra un equipo nuevo y este se guarda con estado disponible en la base
    nuevo = register_equipment(
        inventory_id="MES-00021", serial_number="SN-MES-021",
        name="Mesa ejecutiva", value="450.00", registered_by=mt01,
    )
    guardado = Equipment.objects.get(inventory_id="MES-00021")
    assert (guardado.status, guardado.value, guardado.serial_number) == (EquipmentStatus.AVAILABLE, 450.00, "SN-MES-021")

    # Comprueba que intentar registrar un equipo con un código de inventario ya existente lanza error de validación y preserva la base
    antes = foto_de_la_base()
    with pytest.raises(ValidationError) as error_duplicado:
        register_equipment(
            inventory_id="MES-00021", serial_number="SN-OTRO-99",
            name="Otra mesa", value="200.00", registered_by=mt01,
        )
    assert "inventory_id" in error_duplicado.value.message_dict
    assert foto_de_la_base() == antes