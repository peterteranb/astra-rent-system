"""Entry page after login: it only sends each user to the page of their role."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..roles import MAINTENANCE, OPERATOR, has_role


@login_required
def home(request):
    """After login, send each user to the first page of their role."""
    if request.user.is_superuser:
        return redirect("admin:index")
    if has_role(request.user, OPERATOR):
        return redirect("staff_reservations")
    if has_role(request.user, MAINTENANCE):
        return redirect("maintenance")
    return redirect("catalog")
