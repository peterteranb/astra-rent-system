"""Página del responsable para CU-15: el panel con lo que necesita atención y enlaces al admin."""
from django.shortcuts import render
from django.utils import timezone

from ..dashboard import manager_summary
from ..roles import ADMINISTRATOR, role_required


@role_required(ADMINISTRATOR)
def manager_dashboard(request):
    """Muestra el panel del responsable (CU-15)."""
    return render(request, "rentals/manager_dashboard.html", {"summary": manager_summary(timezone.now())})
