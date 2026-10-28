"""Roles del sistema y el decorador que reserva cada página para su rol (RF-19)."""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from accounts.models import Role

CLIENT = Role.CLIENT
OPERATOR = Role.OPERATOR
MAINTENANCE = Role.MAINTENANCE
ADMINISTRATOR = Role.ADMINISTRATOR


def has_role(user, role) -> bool:
    """Devuelve True si el usuario tiene el rol o es administrador (ENT-13: el administrador puede todo)."""
    if not user.is_authenticated:
        return False
    return user.role.code in (role, ADMINISTRATOR)


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
