"""Login form with the E2 message of PRE-CU-01."""
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """Django's login form, only with our own text for wrong credentials."""

    # Copy Django's messages and replace only the wrong-credentials one
    # with the provisional text of E2 (Sesión 07).
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña incorrectos.",
    }
