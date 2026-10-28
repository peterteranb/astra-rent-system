"""Páginas del operador para CU-08 y CU-09: entregar los equipos reservados y recibirlos de vuelta.

Leen la petición, llaman a use_cases/handover.py y eligen la plantilla; las reglas están ahí y en rules.py.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.roles import OPERATOR, role_required

from ..errors import OperationRejectedError
from ..forms import ReturnForm
from ..models import Rental
from ..services.formatting import days_text, money_text
from ..statuses import ReturnResult
from ..use_cases.handover import (
    register_pickup,
    register_return,
    rentals_to_receive,
    reservations_to_hand_over,
)


@role_required(OPERATOR)
def staff_reservations(request):
    """Muestra las reservas que el operador puede entregar."""
    return render(
        request, "rentals/staff_reservations.html", {"reservations": reservations_to_hand_over()}
    )


# role_required va afuera: un visitante va al login antes de que require_POST responda 405.
@role_required(OPERATOR)
@require_POST
def pickup_reservation(request, rental_id):
    """Registra el recojo de una reserva, cobrando si el pago estaba pendiente, y vuelve a la lista (CU-08)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    was_pending = not rental.is_paid
    try:
        register_pickup(rental, request.user, paid_now=request.POST.get("paid_now") == "yes")
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, pickup_message(rental, was_pending))
    # Redirige después del POST: recargar la página no lo envía otra vez.
    return redirect("staff_reservations")


def pickup_message(rental, was_pending):
    """Mensaje de éxito del recojo; si se cobró en ese momento, empieza con el cobro."""
    handed_over = f"{rental.equipment.inventory_id} entregado a {rental.client.username}."
    if was_pending:
        return f"Cobro de {money_text(rental.total_price)} en efectivo y recojo registrados: {handed_over}"
    return f"Recojo registrado: {handed_over}"


@role_required(OPERATOR)
def staff_returns(request):
    """Muestra las rentas que faltan devolver, con su estado."""
    return render(request, "rentals/staff_returns.html", {"rentals": rentals_to_receive()})


@role_required(OPERATOR)
def return_rental(request, rental_id):
    """Muestra el formulario de la observación de una renta y registra la devolución (CU-09)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    form = ReturnForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            returned = register_return(rental, request.user, form.cleaned_data["note"])
        except OperationRejectedError as error:
            # Se queda en el formulario para que el operador corrija la observación.
            form.add_error(None, str(error))
        else:
            messages.success(request, return_message(returned))
            return redirect("staff_returns")
    return render(request, "rentals/return_form.html", {"rental": rental, "form": form})


def return_message(rental):
    """Mensaje de éxito de una devolución, que termina con cómo llegó y, con atraso, la deuda (RF-09)."""
    received = f"Devolución registrada: {rental.equipment.inventory_id} recibido de {rental.client.username}."
    if rental.return_result != ReturnResult.LATE:
        return f"{received} {rental.return_result.label}."
    return f"{received} Con {days_text(rental.late_days)} de atraso: deuda de {money_text(rental.late_charge)}."
