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
    """Devuelve los equipos que no están de baja, filtrados por ?status=, con sus estados posibles y su último cliente."""
    return success([entry_data(entry) for entry in review_queue(request.GET.get("status", ""))])


def entry_data(entry):
    """Un equipo de la lista de mantenimiento: sus opciones y a quién se le cobraría el daño."""
    last_rental = entry.last_rental
    return {
        **equipment_data(entry.equipment),
        "choices": [{"value": value, "label": label} for value, label in entry.choices],
        "last_client": last_rental.client.username if last_rental else None,
        "charge_label": entry.charge_label,
    }


@api_view("POST", roles=[MAINTENANCE])
def review_equipment_view(request, inventory_id):
    """Guarda la decisión de mantenimiento sobre un equipo (CU-10)."""
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)
    body = read_json(request)
    outcome = review_equipment(
        equipment,
        request.user,
        str(body.get("status", "")),
        str(body.get("comment", "")),
        charge_last_client=body.get("charge_last_client") is True,
    )
    return success(
        {
            **equipment_data(outcome.change.equipment),
            "debt": debt_data(outcome.debt) if outcome.debt else None,
            "cancelled_rentals": [rental.pk for rental in outcome.cancelled],
        },
        review_message(outcome),
    )
