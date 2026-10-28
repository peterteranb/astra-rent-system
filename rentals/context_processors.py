"""Variables de plantilla que le dicen a base.html qué enlaces mostrar según el rol (RF-19)."""
from .roles import ADMINISTRATOR, MAINTENANCE, OPERATOR, has_role, is_store_staff


def staff_roles(request):
    """Devuelve is_store_staff, is_operator, is_maintenance e is_admin para el usuario de la petición."""
    return {
        "is_store_staff": is_store_staff(request.user),
        "is_operator": has_role(request.user, OPERATOR),
        "is_maintenance": has_role(request.user, MAINTENANCE),
        "is_admin": has_role(request.user, ADMINISTRATOR),
    }
