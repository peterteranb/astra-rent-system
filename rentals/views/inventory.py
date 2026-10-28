"""Página del administrador para CU-12: registrar un equipo nuevo.

Lee la petición, llama a inventory.py y elige la plantilla; las reglas están en el modelo Equipment.
"""
from django.contrib import messages
from django.shortcuts import redirect, render

from ..errors import RejectedWithCausesError
from ..forms import EquipmentForm
from ..inventory import register_equipment
from ..roles import ADMINISTRATOR, role_required


@role_required(ADMINISTRATOR)
def register_equipment_view(request):
    """Muestra el formulario de un equipo nuevo y lo registra (CU-12)."""
    form = EquipmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            equipment = register_equipment(**form.cleaned_data)
        except RejectedWithCausesError as error:
            for cause in error.causes:
                form.add_error(None, cause)
        else:
            messages.success(request, f"Equipo registrado: {equipment}.")
            return redirect("register_equipment")
    return render(request, "rentals/equipment_form.html", {"form": form})
