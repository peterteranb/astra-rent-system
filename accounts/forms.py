"""Formularios de cuentas: el registro de clientes, el login con nuestros mensajes (RC-04) y los del admin de usuarios."""
import logging

from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, AuthenticationForm, UserChangeForm

from rentals.services.events import log_event

from .registration import normalize_phone


class LoginForm(AuthenticationForm):
    """El login de Django con nuestros textos para credenciales incorrectas y para la cuenta desactivada."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña incorrectos.",
        "inactive": "Tu cuenta está desactivada. Comunícate con la tienda.",
    }

    def confirm_login_allowed(self, user):
        """Rechaza la cuenta desactivada y lo escribe en el log (ENT-79).

        Solo se llega aquí con la contraseña correcta: con una incorrecta se ve el mensaje general,
        así no se da pistas a quien adivina cuentas.
        """
        if not user.is_active:
            log_event("LOGIN_REJECTED", logging.WARNING, reason="inactive", user=user.username)
        super().confirm_login_allowed(user)


class SignUpForm(forms.Form):
    """Los datos de una cuenta nueva, en la web (CU-01) o en la tienda (CU-02).

    Ningún campo es obligatorio aquí: register_client revisa todo al presionar el
    botón y muestra todas las causas juntas (RC-04).
    """

    first_name = forms.CharField(label="Nombre", required=False, max_length=150)
    last_name = forms.CharField(label="Apellido", required=False, max_length=150)
    email = forms.CharField(label="Correo", required=False, max_length=254)
    phone = forms.CharField(
        label="Teléfono", required=False, max_length=20, help_text="Solo números, de 7 a 15."
    )
    username = forms.CharField(
        label="Usuario",
        required=False,
        max_length=150,
        help_text="Con él inicias sesión. Letras, números y @ . + - _",
    )
    # render_value=False: si se rechaza, la contraseña no vuelve a la página.
    password = forms.CharField(
        label="Contraseña",
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Mínimo 8 caracteres, una mayúscula y un número.",
    )
    password_confirmation = forms.CharField(
        label="Repetir contraseña",
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
    )


class PhoneCleaningMixin:
    """Guarda el teléfono solo con dígitos, igual que el registro de clientes."""

    def clean_phone(self):
        """Devuelve el teléfono escrito, sin espacios ni guiones."""
        return normalize_phone(self.cleaned_data["phone"])


class UserCreationAdminForm(PhoneCleaningMixin, AdminUserCreationForm):
    """Alta de un usuario en el admin, con el teléfono normalizado."""


class UserChangeAdminForm(PhoneCleaningMixin, UserChangeForm):
    """Edición de un usuario en el admin, con el teléfono normalizado."""
