"""Caso de uso CU-01 y CU-02: crear la cuenta de un cliente, en la web con su contraseña o en la tienda sin ella.

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
from rentals.services.events import log_event, logs_rejection, user_text
from rentals.services.notifications import send_create_password, send_welcome

from .models import PHONE_FORMAT, PHONE_FORMAT_MESSAGE, Role, User

REJECTION_TITLE = "No se creó la cuenta:"

PROFILE_FIELDS = [
    ("first_name", "Nombre"),
    ("last_name", "Apellido"),
    ("email", "Correo"),
    ("phone", "Teléfono"),
]
ACCOUNT_FIELDS = [*PROFILE_FIELDS, ("username", "Usuario")]
PASSWORD_FIELDS = [("password", "Contraseña"), ("password_confirmation", "Repetir contraseña")]


@dataclass(frozen=True)
class SignUpData:
    """Lo que escribió la persona en el formulario de registro, tal cual; en la tienda no hay contraseña."""

    first_name: str
    last_name: str
    email: str
    phone: str
    username: str
    password: str = ""
    password_confirmation: str = ""


@dataclass(frozen=True)
class StoreRegistration:
    """La cuenta creada en la tienda y si salió el correo para que el cliente cree su contraseña."""

    user: User
    email_sent: bool


def normalize_phone(text):
    """Deja solo los dígitos del teléfono: «7123-4567» y «71234567» son el mismo número."""
    return "".join(character for character in text if character.isdigit())


def attempted_account(data, registered_by=None, site_url=""):
    """El usuario y el correo que se intentaron registrar, para el log del rechazo; nunca la contraseña."""
    return {"username": data.username.strip(), "email": data.email.strip(), "by": channel_actor(registered_by)}


def channel_actor(registered_by):
    """Devuelve quién creó la cuenta: el operador en la tienda o «web»."""
    return registered_by.username if registered_by else "web"


@logs_rejection("ACCOUNT_REJECTED", attempted_account)
def register_client(data) -> User:
    """Crea la cuenta que el cliente pide en la web, con su contraseña cifrada, y la devuelve (CU-01, ENT-15, ENT-84).

    Lanza RegistrationRejectedError con todas las causas si alguna regla falla; entonces no se guarda nada.
    """
    data = cleaned(data)
    check_new_client(data, with_password=True)
    user = new_client(data)
    # set_password guarda un hash, nunca la contraseña tal cual.
    user.set_password(data.password)
    save_client(user, registered_by=None)
    send_welcome(user)
    return user


@logs_rejection("ACCOUNT_REJECTED", attempted_account)
def register_store_client(data, registered_by, site_url) -> StoreRegistration:
    """Crea la cuenta que el operador registra en la tienda, sin contraseña, y le manda al cliente el enlace para crearla.

    CU-02, ENT-102: el operador nunca conoce la contraseña del cliente. site_url es la dirección
    del sistema, para armar el enlace. Lanza RegistrationRejectedError como register_client.
    """
    data = cleaned(data)
    check_new_client(data, with_password=False)
    user = new_client(data)
    user.set_unusable_password()
    save_client(user, registered_by)
    # En el momento y sin on_commit: la cuenta ya existe y el operador sabe al instante si el correo salió (D-37).
    return StoreRegistration(user, send_create_password(user, site_url))


def new_client(data) -> User:
    """Arma la cuenta del cliente sin guardarla y sin contraseña."""
    return User(
        username=data.username,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=Role.objects.get(code=Role.CLIENT),
    )


def save_client(user, registered_by):
    """Guarda la cuenta y escribe ACCOUNT_CREATED; lanza RegistrationRejectedError si la base la rechaza."""
    # Sin fila que bloquear: si dos piden el mismo usuario, correo o teléfono, el índice único rechaza al segundo.
    try:
        with transaction.atomic():
            user.save()
    except IntegrityError as error:
        raise RegistrationRejectedError(
            REJECTION_TITLE, ["El usuario, el correo o el teléfono ya están registrados."]
        ) from error
    log_event(
        "ACCOUNT_CREATED",
        user=user_text(user),
        email=user.email,
        role=Role.CLIENT,
        channel="store" if registered_by else "web",
        by=channel_actor(registered_by),
    )


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


def check_new_client(data, with_password):
    """Lanza RegistrationRejectedError con todas las causas; primero las que no consultan la base."""
    password_fields = PASSWORD_FIELDS if with_password else []
    causes = [
        *missing_fields(data, [*ACCOUNT_FIELDS, *password_fields]),
        *format_causes(data),
        *(password_causes(data) if with_password else []),
        *taken_causes(data),
    ]
    if causes:
        raise RegistrationRejectedError(REJECTION_TITLE, causes)


def missing_fields(data, fields):
    """Devuelve «Falta el campo X.» por cada campo de fields que está vacío."""
    return [f"Falta el campo {label}." for field, label in fields if not getattr(data, field)]


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


def taken_causes(data, current_user=None):
    """Devuelve las causas de un usuario, correo o teléfono que ya tiene otra cuenta; current_user no cuenta."""
    others = User.objects.exclude(pk=current_user.pk) if current_user else User.objects.all()
    causes = []
    if data.username and others.filter(username__iexact=data.username).exists():
        causes.append(f"El usuario {data.username} ya existe.")
    if data.email and others.filter(email__iexact=data.email).exists():
        causes.append("El correo ya está registrado.")
    if data.phone and others.filter(phone=data.phone).exists():
        causes.append("El teléfono ya está registrado.")
    return causes


def is_valid(validator, value) -> bool:
    """Devuelve True si el validador de Django acepta el valor."""
    try:
        validator(value)
    except ValidationError:
        return False
    return True
