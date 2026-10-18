"""Template variables that tell base.html which staff links to show."""
from .roles import MAINTENANCE, OPERATOR, has_role


def staff_roles(request):
    """Return is_operator and is_maintenance for the user of the request."""
    return {
        "is_operator": has_role(request.user, OPERATOR),
        "is_maintenance": has_role(request.user, MAINTENANCE),
    }
