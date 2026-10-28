"""Caso de uso CU-01 y CU-02: crear la cuenta de un cliente, en la web o en la tienda, con la misma función.

Revisa todas las reglas al presionar «Registrarme» y devuelve todas las causas juntas (RC-04).
"""
import re
from dataclasses import dataclass

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction

from rentals.errors import RegistrationRejectedError
from rentals.events import log_event, logs_rejection
from rentals.notifications import send_welcome

from .models import PHONE_FORMAT, PHONE_FORMAT_MESSAGE, Role, User

REJECTION_TITLE = "No se creó la cuenta:"

REQUIRED_FIELDS = [
    ("first_name", "Nombre"),
    ("last_name", "Apellido"),
    ("email", "Correo"),
    ("phone", "Teléfono"),
    ("username", "Usuario"),
    ("password", "Contraseña"),
    ("password_confirmation", "Repetir contraseña"),
]


@dataclass(frozen=True)
class SignUpData:
    """Lo que escribió la persona en el formulario de registro, tal cual."""

    first_name: str
    last_name: str
    email: str
    phone: str
    username: str
    password: str
    password_confirmation: str


def normalize_phone(text):
    """Deja solo los dígitos del teléfono: «7123-4567» y «71234567» son el mismo número."""
    return "".join(character for character in text if character.isdigit())


@logs_rejection("ACCOUNT_REJECTED")
def register_client(data, registered_by=None) -> User:
    """Crea la cuenta de un cliente con su contraseña cifrada y la devuelve (ENT-15, ENT-84).

    registered_by es el operador que la crea en la tienda; None si la crea el
    cliente en la web. Lanza RegistrationRejectedError con todas las causas si
    alguna regla falla; entonces no se guarda nada.
    """
    data = cleaned(data)
    check_new_client(data)
    user = User(
        username=data.username,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=Role.objects.get(code=Role.CLIENT),
    )
    # set_password guarda un hash, nunca la contraseña tal cual.
    user.set_password(data.password)
    # No hay fila que bloquear: si dos personas eligen el mismo usuario, correo o
    # teléfono a la vez, los índices únicos de la base rechazan a la segunda.
    try:
        with transaction.atomic():
            user.save()
    except IntegrityError as error:
        raise RegistrationRejectedError(
            REJECTION_TITLE, ["El usuario, el correo o el teléfono ya están registrados."]
        ) from error
    log_event(
        "ACCOUNT_CREATED",
        id=user.pk,
        username=user.username,
        role=Role.CLIENT,
        registered_by=registered_by.username if registered_by else "web",
    )
    send_welcome(user)
    return user


def cleaned(data):
    """Quita los espacios de los textos y deja el teléfono solo con dígitos; las contraseñas no se tocan."""
    return SignUpData(
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        email=data.email.strip(),
        phone=normalize_phone(data.phone),
        username=data.username.strip(),
        password=data.password,
        password_confirmation=data.password_confirmation,
    )


def check_new_client(data):
    """Lanza RegistrationRejectedError con todas las causas; primero las que no consultan la base."""
    causes = [
        *missing_fields(data),
        *format_causes(data),
        *password_causes(data),
        *taken_causes(data),
    ]
    if causes:
        raise RegistrationRejectedError(REJECTION_TITLE, causes)


def missing_fields(data):
    """Devuelve «Falta el campo X.» por cada campo vacío."""
    return [f"Falta el campo {label}." for field, label in REQUIRED_FIELDS if not getattr(data, field)]


def format_causes(data):
    """Devuelve las causas de un correo, un teléfono o un usuario con forma inválida."""
    causes = []
    if data.email and not is_valid(validate_email, data.email):
        causes.append("El correo no es válido.")
    if data.phone and not re.fullmatch(PHONE_FORMAT, data.phone):
        causes.append(PHONE_FORMAT_MESSAGE)
    if data.username and not is_valid(UnicodeUsernameValidator(), data.username):
        causes.append("El usuario solo puede tener letras, números y los signos @ . + - _")
    return causes


def password_causes(data):
    """Devuelve las causas de la contraseña: que coincida y que pase AUTH_PASSWORD_VALIDATORS."""
    if not data.password:
        return []
    causes = []
    if data.password_confirmation and data.password != data.password_confirmation:
        causes.append("Las contraseñas no coinciden.")
    # El usuario sin guardar permite al validador de similitud comparar con el nombre y el correo.
    candidate = User(
        username=data.username, first_name=data.first_name, last_name=data.last_name, email=data.email
    )
    try:
        validate_password(data.password, user=candidate)
    except ValidationError as error:
        causes.extend(error.messages)
    return causes


def taken_causes(data):
    """Devuelve las causas de un usuario, correo o teléfono que ya tiene otra cuenta."""
    causes = []
    if data.username and User.objects.filter(username__iexact=data.username).exists():
        causes.append(f"El usuario {data.username} ya existe.")
    if data.email and User.objects.filter(email__iexact=data.email).exists():
        causes.append("El correo ya está registrado.")
    if data.phone and User.objects.filter(phone=data.phone).exists():
        causes.append("El teléfono ya está registrado.")
    return causes


def is_valid(validator, value) -> bool:
    """Devuelve True si el validador de Django acepta el valor."""
    try:
        validator(value)
    except ValidationError:
        return False
    return True
