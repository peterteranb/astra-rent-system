"""Prueba accounts/validators.py: UppercaseAndDigitValidator, la regla propia de contraseña (ENT-84),
y accounts/registration.py: normalize_phone(), que deja el teléfono solo con dígitos."""
import pytest
from django.core.exceptions import ValidationError

from accounts.registration import normalize_phone
from accounts.validators import UppercaseAndDigitValidator


def test_una_contrasena_con_mayuscula_y_numero_se_acepta():
    # «Abcdefg1» tiene mayúscula y número -> se acepta, no lanza error
    assert UppercaseAndDigitValidator().validate("Abcdefg1") is None


def test_una_contrasena_sin_mayuscula_se_rechaza():
    # «abcdefg1» no tiene mayúscula -> rechazada con la causa
    with pytest.raises(ValidationError) as error:
        UppercaseAndDigitValidator().validate("abcdefg1")
    assert error.value.messages == ["La contraseña necesita al menos una mayúscula."]


def test_una_contrasena_sin_numero_se_rechaza():
    # «Abcdefgh» no tiene número -> rechazada con la causa
    with pytest.raises(ValidationError) as error:
        UppercaseAndDigitValidator().validate("Abcdefgh")
    assert error.value.messages == ["La contraseña necesita al menos un número."]


def test_el_telefono_queda_solo_con_digitos():
    # Escribe «+591 7123-4567» -> se guarda 59171234567
    assert normalize_phone("+591 7123-4567") == "59171234567"
