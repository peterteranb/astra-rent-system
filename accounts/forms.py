"""Formularios de cuentas: el registro de clientes, el login con nuestros mensajes (RC-04), «Mi cuenta», las contraseñas y los del admin de usuarios."""
import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserChangeForm,
)

from rentals.services.events import log_event, user_text

from .registration import normalize_phone

RESET_EMAIL_TEMPLATE = "accounts/password_reset_email.txt"
RESET_SUBJECT_TEMPLATE = "accounts/password_reset_subject.txt"


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


class ProfileForm(forms.Form):
    """Los datos personales de una cuenta: nombre, apellido, correo y teléfono (CU-17).

    Ningún campo es obligatorio aquí: el caso de uso revisa todo al presionar el
    botón y muestra todas las causas juntas (RC-04).
    """

    first_name = forms.CharField(label="Nombre", required=False, max_length=150)
    last_name = forms.CharField(label="Apellido", required=False, max_length=150)
    email = forms.CharField(label="Correo", required=False, max_length=254)
    phone = forms.CharField(
        label="Teléfono", required=False, max_length=20, help_text="Solo números, de 7 a 15."
    )


class StoreSignUpForm(ProfileForm):
    """Los datos de una cuenta que el operador crea en la tienda (CU-02): sin contraseña (ENT-102)."""

    username = forms.CharField(
        label="Usuario",
        required=False,
        max_length=150,
        help_text="Con él inicias sesión. Letras, números y @ . + - _",
    )


class SignUpForm(StoreSignUpForm):
    """Los datos de una cuenta que el cliente crea en la web (CU-01), con su contraseña."""

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


class LogsPasswordChangeMixin:
    """Escribe PASSWORD_CHANGED al guardar la contraseña nueva; channel dice desde dónde se cambió."""

    channel = ""

    def save(self, commit=True):
        """Guarda la contraseña con el formulario de Django y escribe el log, sin la contraseña."""
        user = super().save(commit)
        log_event("PASSWORD_CHANGED", user=user_text(user), channel=self.channel, by=user.username)
        return user


class AccountPasswordChangeForm(LogsPasswordChangeMixin, PasswordChangeForm):
    """Cambiar la contraseña desde «Mi cuenta»: pide la actual y usa AUTH_PASSWORD_VALIDATORS (CU-17)."""

    channel = "account"


class ResetSetPasswordForm(LogsPasswordChangeMixin, SetPasswordForm):
    """Crear la contraseña nueva desde el enlace del correo, al recuperarla o al crearla después de la tienda."""

    channel = "reset"


class ClientPasswordResetForm(PasswordResetForm):
    """«Olvidé mi contraseña» de Django, que también sirve a la cuenta creada en la tienda (ENT-102)."""

    def get_users(self, email):
        """Devuelve las cuentas activas con ese correo, también las que todavía no tienen contraseña.

        El de Django las omite, y entonces el cliente de la tienda nunca recibiría el enlace.
        """
        return get_user_model()._default_manager.filter(email__iexact=email, is_active=True)

    def save(self, *args, **kwargs):
        """Escribe PASSWORD_RESET_REQUESTED con el correo pedido y la cuenta encontrada, y manda el enlace."""
        email = self.cleaned_data["email"]
        users = ",".join(user.username for user in self.get_users(email)) or "-"
        log_event("PASSWORD_RESET_REQUESTED", email=email, users=users, by="web")
        super().save(*args, **kwargs)


class PhoneCleaningMixin:
    """Guarda el teléfono solo con dígitos, igual que el registro de clientes."""

    def clean_phone(self):
        """Devuelve el teléfono escrito, sin espacios ni guiones."""
        return normalize_phone(self.cleaned_data["phone"])


class UserCreationAdminForm(PhoneCleaningMixin, AdminUserCreationForm):
    """Alta de un usuario en el admin, con el teléfono normalizado."""


class UserChangeAdminForm(PhoneCleaningMixin, UserChangeForm):
    """Edición de un usuario en el admin, con el teléfono normalizado."""
