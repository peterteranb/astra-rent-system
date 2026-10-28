"""Validador propio de contraseñas, que se suma a los de Django en AUTH_PASSWORD_VALIDATORS."""
from django.core.exceptions import ValidationError


class UppercaseAndDigitValidator:
    """Pide al menos una mayúscula y un número en la contraseña (ENT-84)."""

    def validate(self, password, user=None):
        """Lanza ValidationError con cada requisito que le falta a la contraseña."""
        errors = []
        if not any(character.isupper() for character in password):
            errors.append(
                ValidationError("La contraseña necesita al menos una mayúscula.", code="no_uppercase")
            )
        if not any(character.isdigit() for character in password):
            errors.append(
                ValidationError("La contraseña necesita al menos un número.", code="no_digit")
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        """Texto de ayuda que se muestra antes de escribir la contraseña."""
        return "Tu contraseña necesita al menos una mayúscula y un número."
