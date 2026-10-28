"""Página de entrada después del login: solo manda a cada usuario a la página de su rol."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..roles import ADMINISTRATOR, MAINTENANCE, OPERATOR, has_role


@login_required
def home(request):
    """Manda a cada usuario a la primera página de su rol (RF-19)."""
    if has_role(request.user, ADMINISTRATOR):
        return redirect("manager_dashboard")
    if has_role(request.user, OPERATOR):
        return redirect("staff_reservations")
    if has_role(request.user, MAINTENANCE):
        return redirect("maintenance")
    return redirect("catalog")
