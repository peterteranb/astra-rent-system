"""Prueba accounts/validators.py (contraseñas seguras) y accounts/registration.py (normalización de teléfonos)."""
import pytest
from django.core.exceptions import ValidationError

from accounts.registration import normalize_phone
from accounts.validators import UppercaseAndDigitValidator


def test_validaciones_de_contrasena_y_normalizacion_de_telefono():
    # Clave «Abcdefg1» con mayúscula y número se acepta; sin mayúscula («abcdefg1») o sin número («Abcdefgh») se rechazan con su respectivo mensaje -> robustez de claves
    # Comprueba que una contraseña con mayúscula y número se acepta sin errores
    assert UppercaseAndDigitValidator().validate("Abcdefg1") is None
    # Comprueba que una contraseña sin mayúsculas es rechazada con su mensaje específico
    with pytest.raises(ValidationError) as error_mayus:
        UppercaseAndDigitValidator().validate("abcdefg1")
    assert error_mayus.value.messages == ["La contraseña necesita al menos una mayúscula."]
    # Comprueba que una contraseña sin números es rechazada con su mensaje específico
    with pytest.raises(ValidationError) as error_num:
        UppercaseAndDigitValidator().validate("Abcdefgh")
    assert error_num.value.messages == ["La contraseña necesita al menos un número."]

    # Escribe «+591 7123-4567» -> se normaliza dejando únicamente los dígitos (59171234567) -> limpieza de formato telefónico
    # Comprueba que el teléfono se limpia de caracteres especiales y conserva solo los dígitos
    assert normalize_phone("+591 7123-4567") == "59171234567"