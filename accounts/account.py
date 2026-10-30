"""Caso de uso CU-17: el usuario edita sus datos (ENT-103); cambiar y recuperar la contraseña lo hacen las vistas de Django."""
from django.db import IntegrityError, transaction

from rentals.errors import RegistrationRejectedError
from rentals.services.events import log_event, logs_rejection, user_text

from .models import User
from .registration import PROFILE_FIELDS, SignUpData, cleaned, format_causes, missing_fields, taken_causes

PROFILE_REJECTION_TITLE = "No se guardaron tus datos:"


def attempted_profile(user, first_name, last_name, email, phone):
    """La cuenta que se quiso editar, para el log del rechazo; los datos escritos no se escriben."""
    return {"user": user_text(user), "by": user.username}


@logs_rejection("PROFILE_REJECTED", attempted_profile)
def update_profile(user, first_name, last_name, email, phone) -> User:
    """Guarda el nombre, apellido, correo y teléfono de user con las reglas del registro y devuelve la cuenta.

    El usuario y el rol no cambian. Lanza RegistrationRejectedError con todas las causas; entonces no se guarda nada.
    """
    data = cleaned(SignUpData(first_name, last_name, email, phone, user.username))
    check_profile(data, user)
    try:
        with transaction.atomic():
            # Bloquea la fila: dos ediciones a la vez no se pisan.
            locked_user = User.objects.select_for_update().get(pk=user.pk)
            changed = changed_fields(locked_user, data)
            for field in changed:
                setattr(locked_user, field, getattr(data, field))
            locked_user.save(update_fields=changed)
    except IntegrityError as error:
        raise RegistrationRejectedError(
            PROFILE_REJECTION_TITLE, ["El correo o el teléfono ya están registrados."]
        ) from error
    # Solo los nombres de los campos: el log no guarda el correo ni el teléfono nuevos.
    log_event("PROFILE_UPDATED", user=user_text(locked_user), fields=",".join(changed) or "-", by=user.username)
    return locked_user


def check_profile(data, user):
    """Lanza RegistrationRejectedError con todas las causas: campos vacíos, formato y datos de otra cuenta."""
    causes = [*missing_fields(data, PROFILE_FIELDS), *format_causes(data), *taken_causes(data, current_user=user)]
    if causes:
        raise RegistrationRejectedError(PROFILE_REJECTION_TITLE, causes)


def changed_fields(user, data) -> list[str]:
    """Devuelve los campos del perfil cuyo valor nuevo es distinto del guardado."""
    return [field for field, _label in PROFILE_FIELDS if getattr(user, field) != getattr(data, field)]
