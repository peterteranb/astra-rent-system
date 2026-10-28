"""Formato común de la API: éxito {"data", "message"}, rechazo {"errors"} y el decorador que revisa método, sesión y rol."""
import json
from functools import wraps

from django.core.exceptions import BadRequest
from django.http import Http404, JsonResponse
from django.views.csrf import csrf_failure as html_csrf_failure

from accounts.roles import has_role

from ..errors import OperationRejectedError, RejectedWithCausesError

NOT_LOGGED_IN = "Inicia sesión para continuar."
NO_PERMISSION = "No tienes permiso para hacer esto."
NOT_FOUND = "No encontramos lo que buscas."
METHOD_NOT_ALLOWED = "Esta dirección no acepta ese método."
CSRF_REJECTED = "La sesión de seguridad venció. Recarga la página e inténtalo de nuevo."
INVALID_BODY = "La petición debe traer un objeto JSON."


def success(data=None, message="", status=200):
    """Responde {"data": data, "message": message} con el código status."""
    return JsonResponse({"data": data, "message": message}, status=status)


def failure(errors, status=400):
    """Responde {"errors": [...]} con el código status; cada error es un texto para el usuario."""
    return JsonResponse({"errors": list(errors)}, status=status)


def api_view(*methods, roles=(), public=False):
    """Envuelve una vista de la API: revisa método, sesión y rol, y convierte cada rechazo en JSON.

    Sin roles basta con tener sesión; public la abre también a los visitantes.
    """

    def decorator(view):
        """Envuelve la vista con las revisiones y la conversión de errores."""

        @wraps(view)
        def wrapper(request, *args, **kwargs):
            """Responde 405, 401 o 403 antes de abrir la vista; si no, la llama y atrapa sus rechazos."""
            if request.method not in methods:
                return failure([METHOD_NOT_ALLOWED], 405)
            if not public and not request.user.is_authenticated:
                return failure([NOT_LOGGED_IN], 401)
            if roles and not any(has_role(request.user, role) for role in roles):
                return failure([NO_PERMISSION], 403)
            return call_view(view, request, *args, **kwargs)

        return wrapper

    return decorator


def call_view(view, request, *args, **kwargs):
    """Llama a la vista y convierte el 404, la petición mal armada y el rechazo de una regla en JSON."""
    try:
        return view(request, *args, **kwargs)
    except Http404:
        return failure([NOT_FOUND], 404)
    except BadRequest as error:
        return failure([str(error)])
    except RejectedWithCausesError as error:
        return failure(error.causes)
    except OperationRejectedError as error:
        return failure([str(error)])


def read_json(request):
    """Devuelve el cuerpo JSON de la petición como diccionario; lanza BadRequest si no lo es."""
    try:
        body = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError) as error:
        raise BadRequest(INVALID_BODY) from error
    if not isinstance(body, dict):
        raise BadRequest(INVALID_BODY)
    return body


class FormRejectedError(RejectedWithCausesError):
    """Los campos de la petición no tienen la forma esperada: falta uno o no es una fecha válida."""

    def __init__(self, causes):
        """Guarda las causas sin título: la API las devuelve como lista."""
        super().__init__("", causes)


def valid_form(form):
    """Devuelve los datos limpios del formulario; si no es válido, lanza FormRejectedError con sus errores."""
    if form.is_valid():
        return form.cleaned_data
    raise FormRejectedError(form_errors(form))


def form_errors(form):
    """Devuelve los errores del formulario como textos, cada uno con la etiqueta de su campo."""
    errors = []
    for field, messages in form.errors.items():
        label = form.fields[field].label if field in form.fields else ""
        errors.extend(f"{label}: {message}" if label else message for message in messages)
    return errors


def not_found(request, *args, **kwargs):
    """Responde 404 en JSON a una dirección de la API que no existe."""
    return failure([NOT_FOUND], 404)


def csrf_failure(request, reason=""):
    """Responde 403 en JSON si la API llega sin el token CSRF; las páginas ven su plantilla de siempre."""
    if request.path.startswith("/api/"):
        return failure([CSRF_REJECTED], 403)
    return html_csrf_failure(request, reason=reason)
