"""Log de negocio: una línea por operación, aceptada o rechazada, en la consola y en logs/negocio.log (RC-05).

Formato: «2026-10-29 10:15:02 | INFO    | RENTAL_CREATED id=12 equipment=SIL-00001 client=cl01 paid=no».
Nunca se escribe una contraseña.
"""
import logging
from functools import wraps

from .errors import OperationRejectedError

logger = logging.getLogger("rentals")


def log_event(event, level=logging.INFO, **fields):
    """Escribe el evento con sus campos como «EVENTO campo=valor campo="texto con espacios"»."""
    parts = [event, *(f"{name}={field_text(value)}" for name, value in fields.items())]
    logger.log(level, " ".join(parts))


def field_text(value):
    """Escribe un valor del log; si tiene espacios o está vacío, entre comillas."""
    text = str(value).replace('"', "'")
    if not text or " " in text:
        return f'"{text}"'
    return text


def logs_rejection(event):
    """Decora un caso de uso: si se rechaza, escribe event con la causa y nivel WARNING, y deja pasar el error."""

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
                    log_event(event, logging.WARNING, reason=str(error))
                    error.logged = True
                raise

        return wrapper

    return decorator
