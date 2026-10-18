"""Operator pages to hand over reserved units and receive them back.

They read the request, call handover.py and choose a template; the
business rules live in handover.py and rules.py.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..errors import OperationRejectedError
from ..handover import register_pickup, reservations_to_hand_over
from ..models import Rental
from ..roles import OPERATOR, role_required


@role_required(OPERATOR)
def staff_reservations(request):
    """Show the reservations the operator can hand over (C2)."""
    return render(
        request, "rentals/staff_reservations.html", {"reservations": reservations_to_hand_over()}
    )


# role_required goes outside so a visitor is sent to the login before
# require_POST answers 405 to a GET.
@role_required(OPERATOR)
@require_POST
def pickup_reservation(request, rental_id):
    """Register the pickup of one reservation and go back to the list (C2)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    try:
        register_pickup(rental, request.user)
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            f"Recojo registrado: {rental.equipment.inventory_id} entregado a {rental.client.username}.",
        )
    # Redirect after the POST so reloading the page does not send it again.
    return redirect("staff_reservations")


@role_required(OPERATOR)
def staff_returns(request):
    """Operator page to register returns (under construction)."""
    return render(request, "rentals/under_construction.html", {"page_title": "Devoluciones"})
