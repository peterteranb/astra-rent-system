"""Página del administrador para CU-12: registrar un equipo nuevo.

Lee la petición, llama a use_cases/inventory.py y elige la plantilla; las reglas están en el modelo Equipment.
"""
from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.roles import ADMINISTRATOR, role_required

from ..errors import RejectedWithCausesError
from ..forms import EquipmentForm
from ..services.formatting import equipment_registered_message
from ..use_cases.inventory import REJECTION_TITLE, register_equipment


@role_required(ADMINISTRATOR)
def register_equipment_view(request):
    """Muestra el formulario de un equipo nuevo y lo registra (CU-12)."""
    form = EquipmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            equipment = register_equipment(**form.cleaned_data, registered_by=request.user)
        except RejectedWithCausesError as error:
            error.add_to(form)
        else:
            messages.success(request, equipment_registered_message(equipment))
            return redirect("register_equipment")
    return render(
        request, "rentals/equipment_form.html", {"form": form, "rejection_title": REJECTION_TITLE}
    )
