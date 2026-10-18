"""Maintenance pages: the units to review and the form that saves each decision."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..errors import OperationRejectedError
from ..models import Equipment
from ..review import REVIEW_RESULTS, equipment_to_review, review_equipment
from ..roles import MAINTENANCE, role_required


@role_required(MAINTENANCE)
def maintenance(request):
    """Show the units waiting for review or repair, each with its decision form (D2)."""
    choices = [(status.value, status.label) for status in REVIEW_RESULTS]
    return render(
        request,
        "rentals/maintenance.html",
        {"equipment_list": equipment_to_review(), "review_choices": choices},
    )


# role_required goes outside so a visitor is sent to the login before
# require_POST answers 405 to a GET.
@role_required(MAINTENANCE)
@require_POST
def review_unit(request, inventory_id):
    """Save the decision of maintenance for one unit and go back to the list (D2)."""
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)
    try:
        change = review_equipment(
            equipment,
            request.user,
            request.POST.get("status", ""),
            request.POST.get("comment", "").strip(),
        )
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request, f"{inventory_id} ahora está «{change.get_new_status_display()}»."
        )
    # Redirect after the POST so reloading the page does not send it again.
    return redirect("maintenance")