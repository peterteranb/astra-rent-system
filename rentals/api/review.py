"""API de mantenimiento para CU-10: los equipos por revisar y la decisión sobre cada uno."""
from django.shortcuts import get_object_or_404

from accounts.roles import MAINTENANCE

from ..models import Equipment
from ..services.formatting import review_message
from ..use_cases.review import review_equipment, review_queue
from .responses import api_view, read_json, success
from .serializers import debt_data, equipment_data


@api_view("GET", roles=[MAINTENANCE])
def maintenance_equipment(request):
    """Devuelve los equipos que esperan a mantenimiento, cada uno con los estados que puede elegir."""
    return success(
        [
            {
                **equipment_data(equipment),
                "choices": [{"value": value, "label": label} for value, label in choices],
            }
            for equipment, choices in review_queue()
        ]
    )


@api_view("POST", roles=[MAINTENANCE])
def review_equipment_view(request, inventory_id):
    """Guarda la decisión de mantenimiento sobre un equipo (CU-10)."""
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)
    body = read_json(request)
    outcome = review_equipment(
        equipment, request.user, str(body.get("status", "")), str(body.get("comment", ""))
    )
    return success(
        {
            **equipment_data(outcome.change.equipment),
            "debt": debt_data(outcome.debt) if outcome.debt else None,
            "cancelled_rentals": [rental.pk for rental in outcome.cancelled],
        },
        review_message(outcome),
    )
