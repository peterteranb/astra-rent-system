"""Staff roles and the decorator that keeps each staff page for its role."""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

OPERATOR = "operador"
MAINTENANCE = "mantenimiento"


def has_role(user, role) -> bool:
    """Return True if the user is a superuser or belongs to the role's group."""
    if user.is_superuser:
        return True
    return user.is_authenticated and user.groups.filter(name=role).exists()


def role_required(*roles):
    """Let only users with one of the roles open the view; others get the login or a 403."""

    def decorator(view):
        """Wrap the view with the role check."""

        # Not user_passes_test: it sends a logged-in user without the role to
        # the login, and the login sends a logged-in user back here (a loop).
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            """Send visitors to the login, refuse users without the role, run the view otherwise."""
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not any(has_role(request.user, role) for role in roles):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
