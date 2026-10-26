"""Página de entrada después del login: solo manda a cada usuario a la página de su rol."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..roles import MAINTENANCE, OPERATOR, has_role


@login_required
def home(request):
    """Manda a cada usuario a la primera página de su rol (RF-10)."""
    if request.user.is_superuser:
        return redirect("admin:index")
    if has_role(request.user, OPERATOR):
        return redirect("staff_reservations")
    if has_role(request.user, MAINTENANCE):
        return redirect("maintenance")
    return redirect("catalog")
