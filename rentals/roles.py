"""Roles del personal y el decorador que reserva cada página para su rol (RF-11)."""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

OPERATOR = "operador"
MAINTENANCE = "mantenimiento"


def has_role(user, role) -> bool:
    """Devuelve True si el usuario es superusuario o está en el grupo del rol (ENT-13: el superusuario puede todo)."""
    if user.is_superuser:
        return True
    return user.is_authenticated and user.groups.filter(name=role).exists()


def role_required(*roles):
    """Deja abrir la vista solo a quien tiene uno de los roles; a los demás, el login o un 403."""

    def decorator(view):
        """Envuelve la vista con la revisión del rol."""

        # No se usa user_passes_test: manda al login a un usuario con sesión sin el
        # rol, y el login lo devuelve aquí (un bucle).
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            """Manda al visitante al login, rechaza al usuario sin el rol y si no, abre la vista."""
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not any(has_role(request.user, role) for role in roles):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
