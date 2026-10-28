"""Prueba rentals/use_cases/inventory.py: normalize_inventory_id(), y el formato del código del modelo Equipment
(ENT-83: 3 letras, un guion y 5 números, por ejemplo MES-00001)."""
import pytest
from django.core.exceptions import ValidationError

from rentals.models import Equipment
from rentals.use_cases.inventory import normalize_inventory_id

MENSAJE = "El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001."


def revisar_codigo(codigo):
    """Revisa solo el formato del código, sin la base: clean_fields no consulta si se repite."""
    Equipment(inventory_id=codigo, serial_number="SN-1", name="Mesa", value=1).clean_fields()


def test_el_codigo_se_guarda_sin_espacios_y_en_mayusculas():
    # Escribe « mes-00021 » -> se guarda «MES-00021»
    assert normalize_inventory_id(" mes-00021 ") == "MES-00021"


def test_un_codigo_con_3_letras_y_5_numeros_es_valido():
    # MES-00001 -> válido, no lanza error
    assert revisar_codigo("MES-00001") is None


def test_un_codigo_con_4_numeros_se_rechaza():
    # MES-0001 tiene 4 números -> rechazado con el formato esperado
    with pytest.raises(ValidationError) as error:
        revisar_codigo("MES-0001")
    assert error.value.message_dict["inventory_id"] == [MENSAJE]


def test_un_codigo_con_2_letras_se_rechaza():
    # ME-00001 tiene 2 letras -> rechazado con el formato esperado
    with pytest.raises(ValidationError) as error:
        revisar_codigo("ME-00001")
    assert error.value.message_dict["inventory_id"] == [MENSAJE]
