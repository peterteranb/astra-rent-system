"""Prueba rentals/use_cases/inventory.py y el modelo Equipment: normalización y formato del código de equipo."""
import pytest
from django.core.exceptions import ValidationError

from rentals.models import Equipment
from rentals.use_cases.inventory import normalize_inventory_id

MENSAJE = "El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001."


def revisar_codigo(codigo):
    """Revisa solo el formato del código, sin consultar la base de datos."""
    Equipment(inventory_id=codigo, serial_number="SN-1", name="Mesa", value=1).clean_fields()


def test_normalizacion_y_validaciones_de_formato_de_codigo():
    # Escribe « mes-00021 » con espacios y minúsculas -> se normaliza a «MES-00021» en mayúsculas
    # Comprueba que el código se limpia de espacios y pasa a mayúsculas
    assert normalize_inventory_id(" mes-00021 ") == "MES-00021"

    # MES-00001 es válido; MES-0001 (4 números) y ME-00001 (2 letras) se rechazan con el mensaje esperado -> cumplimiento del patrón estricto
    # Comprueba que un código con 3 letras, un guion y 5 números es válido
    assert revisar_codigo("MES-00001") is None
    # Comprueba que un código con menos números de los requeridos lanza error de validación
    with pytest.raises(ValidationError) as error_numeros:
        revisar_codigo("MES-0001")
    assert error_numeros.value.message_dict["inventory_id"] == [MENSAJE]
    # Comprueba que un código con menos letras de las requeridas lanza error de validación
    with pytest.raises(ValidationError) as error_letras:
        revisar_codigo("ME-00001")
    assert error_letras.value.message_dict["inventory_id"] == [MENSAJE]