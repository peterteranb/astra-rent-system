"""API del operador para CU-08 y CU-09: las reservas por entregar, el recojo, las devoluciones pendientes y la devolución."""
from django.shortcuts import get_object_or_404

from accounts.roles import OPERATOR

from ..forms import ReturnForm
from ..models import Rental
from ..services.formatting import pickup_message, return_message
from ..use_cases.handover import register_pickup, register_return, rentals_to_receive, reservations_to_hand_over
from .responses import api_view, read_json, success, valid_form
from .serializers import rental_data


@api_view("GET", roles=[OPERATOR])
def staff_reservations(request):
    """Devuelve las reservas que el operador puede entregar, la más próxima primero."""
    return success([rental_data(rental) for rental in reservations_to_hand_over()])


@api_view("POST", roles=[OPERATOR])
def pickup_reservation(request, rental_id):
    """Registra el recojo; con paid_now true cobra en efectivo el pago pendiente (CU-08)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    was_pending = not rental.is_paid
    picked_up = register_pickup(rental, request.user, paid_now=read_json(request).get("paid_now") is True)
    return success(rental_data(picked_up), pickup_message(picked_up, was_pending))


@api_view("GET", roles=[OPERATOR])
def staff_returns(request):
    """Devuelve las rentas que faltan devolver, la que vence primero arriba."""
    return success([rental_data(rental) for rental in rentals_to_receive()])


@api_view("POST", roles=[OPERATOR])
def return_rental(request, rental_id):
    """Registra la devolución con la observación de cómo llegó el equipo (CU-09)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    data = valid_form(ReturnForm(read_json(request)))
    returned = register_return(rental, request.user, data["note"])
    return success(rental_data(returned), return_message(returned))
