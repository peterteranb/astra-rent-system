"""Páginas de mantenimiento para CU-10: los equipos con su filtro por estado y el formulario que guarda cada decisión."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.roles import MAINTENANCE, role_required

from ..errors import OperationRejectedError
from ..models import Equipment
from ..services.formatting import review_message
from ..statuses import EquipmentStatus
from ..use_cases.review import review_equipment, review_queue


@role_required(MAINTENANCE)
def maintenance(request):
    """Muestra los equipos que no están de baja, con el filtro por estado y las opciones de cada uno."""
    status = request.GET.get("status", "")
    filters = [choice for choice in EquipmentStatus.choices if choice[0] != EquipmentStatus.RETIRED]
    return render(
        request,
        "rentals/maintenance.html",
        {"entries": review_queue(status), "filters": filters, "status": status},
    )


# role_required va afuera: un visitante va al login antes de que require_POST responda 405.
@role_required(MAINTENANCE)
@require_POST
def review_equipment_view(request, inventory_id):
    """Guarda la decisión de mantenimiento sobre un equipo y vuelve a la lista (CU-10)."""
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)
    try:
        outcome = review_equipment(
            equipment,
            request.user,
            request.POST.get("status", ""),
            request.POST.get("comment", ""),
            charge_last_client=request.POST.get("charge_last_client") == "on",
        )
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, review_message(outcome))
    # Redirige después del POST: recargar la página no lo envía otra vez.
    return redirect("maintenance")
