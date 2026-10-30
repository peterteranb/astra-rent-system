"""Log de negocio: una línea por operación, aceptada o rechazada, en la consola y en logs/negocio.log (RC-05).

Cada línea se entiende sin buscar en la base (ENT-101), por ejemplo:
«PAYMENT_APPROVED rental=60 equipment=SIL-00003 "Silla blanca plegable" client=cl01 "Carla Mendoza"
period=30/10/2026 18:00-01/11/2026 09:00 amount=8.00 by=cl01». Nunca se escribe una contraseña.
"""
import logging
from functools import wraps

from django.utils import timezone

from ..errors import OperationRejectedError

logger = logging.getLogger("rentals")


class Written(str):
    """Texto del log que ya viene armado: se escribe tal cual, sin comillas alrededor."""


def log_event(event, level=logging.INFO, **fields):
    """Escribe el evento con sus campos como «EVENTO campo=valor campo="texto con espacios"»."""
    parts = [event, *(f"{name}={field_text(value)}" for name, value in fields.items())]
    logger.log(level, " ".join(parts))


def field_text(value):
    """Escribe un valor del log; si tiene espacios o está vacío, entre comillas."""
    if isinstance(value, Written):
        return value
    text = str(value).replace('"', "'")
    if not text or " " in text:
        return f'"{text}"'
    return text


def named(code, name):
    """Junta un código y su nombre, por ejemplo «SIL-00003 "Silla blanca plegable"»."""
    return Written(f"{field_text(code)} {field_text(name or '-')}")


def equipment_text(equipment):
    """El equipo como «código "nombre"»."""
    return named(equipment.inventory_id, equipment.name)


def user_text(user):
    """La persona como «usuario "nombre completo"»."""
    return named(user.username, user.get_full_name())


def period_text(start, end):
    """El periodo como «dd/mm/aaaa HH:MM-dd/mm/aaaa HH:MM» en hora de La Paz."""
    return Written(f"{timezone.localtime(start):%d/%m/%Y %H:%M}-{timezone.localtime(end):%d/%m/%Y %H:%M}")


def rental_context(rental, by):
    """Arma los campos que identifican una renta en el log; un pedido rechazado todavía no tiene id ni precio."""
    fields = {"rental": rental.pk} if rental.pk else {}
    fields["equipment"] = equipment_text(rental.equipment)
    fields["client"] = user_text(rental.client)
    fields["period"] = period_text(rental.start_datetime, rental.end_datetime)
    if rental.daily_price is not None:
        fields["amount"] = rental.total_price
    fields["by"] = by
    return fields


def debt_context(debt, by):
    """Arma los campos de una deuda: su id, su motivo y su monto, con los datos de su renta."""
    return {"debt": debt.pk, "charge": debt.reason, **rental_context(debt.rental, by), "amount": debt.amount}


def logs_rejection(event, attempt):
    """Decora un caso de uso: si se rechaza, escribe event con lo que se intentó y la causa, y deja pasar el error.

    attempt recibe los mismos argumentos que el caso de uso y devuelve los campos de lo intentado, con «by».
    """

    def decorator(use_case):
        """Envuelve el caso de uso con el registro de su rechazo."""

        @wraps(use_case)
        def wrapper(*args, **kwargs):
            """Llama al caso de uso y, si lanza un rechazo, lo escribe una sola vez."""
            try:
                return use_case(*args, **kwargs)
            except OperationRejectedError as error:
                # Si el rechazo vino de otro caso de uso que ya lo escribió, no se repite.
                if not getattr(error, "logged", False):
                    log_event(event, logging.WARNING, **rejection_fields(attempt(*args, **kwargs), reason_of(error)))
                    error.logged = True
                raise

        return wrapper

    return decorator


def reason_of(error):
    """Devuelve la causa del rechazo; si tiene varias, todas juntas sin el título del formulario."""
    causes = getattr(error, "causes", None)
    return " ".join(causes) if causes else str(error)


def rejection_fields(attempted, reason):
    """Pone el motivo antes de quién actuó: «… reason="…" by=op01»."""
    fields = dict(attempted)
    by = fields.pop("by")
    return {**fields, "reason": reason, "by": by}
