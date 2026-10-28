"""Formularios de cuentas: el login con nuestro mensaje (RC-04) y los del admin de usuarios."""
from django.contrib.auth.forms import AdminUserCreationForm, AuthenticationForm, UserChangeForm

from .registration import normalize_phone


class LoginForm(AuthenticationForm):
    """El login de Django, solo con nuestro texto para credenciales incorrectas."""

    # Copia los mensajes de Django y cambia solo el de credenciales incorrectas.
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña incorrectos.",
    }


class PhoneCleaningMixin:
    """Guarda el teléfono solo con dígitos, igual que el registro de clientes."""

    def clean_phone(self):
        """Devuelve el teléfono escrito, sin espacios ni guiones."""
        return normalize_phone(self.cleaned_data["phone"])


class UserCreationAdminForm(PhoneCleaningMixin, AdminUserCreationForm):
    """Alta de un usuario en el admin, con el teléfono normalizado."""


class UserChangeAdminForm(PhoneCleaningMixin, UserChangeForm):
    """Edición de un usuario en el admin, con el teléfono normalizado."""
