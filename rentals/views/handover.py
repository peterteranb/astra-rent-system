"""Operator pages to hand over reserved units and receive them back.

They read the request, call handover.py and choose a template; the
business rules live in handover.py and rules.py.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..errors import OperationRejectedError
from ..forms import ReturnForm
from ..handover import (
    register_pickup,
    register_return,
    rentals_to_receive,
    reservations_to_hand_over,
)
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
    """Show the rentals still to be returned, with their status (C5)."""
    return render(request, "rentals/staff_returns.html", {"rentals": rentals_to_receive()})


@role_required(OPERATOR)
def return_rental(request, rental_id):
    """Show the return note form for one rental and register the return (C5)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    form = ReturnForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            returned = register_return(rental, request.user, form.cleaned_data["note"])
        except OperationRejectedError as error:
            # Stay on the form so the operator can fix the note.
            form.add_error(None, str(error))
        else:
            messages.success(request, return_message(returned))
            return redirect("staff_returns")
    return render(request, "rentals/return_form.html", {"rental": rental, "form": form})


def return_message(rental):
    """Success message of a return, ending with how it arrived (C4)."""
    return (
        f"Devolución registrada: {rental.equipment.inventory_id} recibido de "
        f"{rental.client.username}. {rental.return_result.label}."
    )
