"""Páginas de mantenimiento para CU-05: los equipos por revisar y el formulario que guarda cada decisión."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..errors import OperationRejectedError
from ..models import Equipment
from ..review import equipment_to_review, review_choices_for, review_equipment
from ..roles import MAINTENANCE, role_required


@role_required(MAINTENANCE)
def maintenance(request):
    """Muestra los equipos en revisión o en reparación, cada uno con sus opciones de decisión."""
    entries = [(equipment, review_choices_for(equipment)) for equipment in equipment_to_review()]
    return render(request, "rentals/maintenance.html", {"entries": entries})


# role_required va afuera: un visitante va al login antes de que require_POST responda 405.
@role_required(MAINTENANCE)
@require_POST
def review_unit(request, inventory_id):
    """Guarda la decisión de mantenimiento sobre un equipo y vuelve a la lista (CU-05)."""
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)
    try:
        change = review_equipment(
            equipment,
            request.user,
            request.POST.get("status", ""),
            request.POST.get("comment", ""),
        )
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request, f"{inventory_id} ahora está «{change.get_new_status_display()}»."
        )
    # Redirige después del POST: recargar la página no lo envía otra vez.
    return redirect("maintenance")
