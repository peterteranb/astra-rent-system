"""Formulario de login con nuestro mensaje para usuario o contraseña incorrectos (RC-01)."""
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """El login de Django, solo con nuestro texto para credenciales incorrectas."""

    # Copia los mensajes de Django y cambia solo el de credenciales incorrectas.
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña incorrectos.",
    }
