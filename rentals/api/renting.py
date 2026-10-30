"""API de CU-03 a CU-07 y CU-16: catálogo, renta en línea y en tienda, pago QR, modificar, cancelar y «Mis rentas».

Leen la petición, llaman a use_cases/ como las páginas y responden JSON; las reglas están ahí y en rules.py.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.roles import OPERATOR

from ..forms import CatalogFilterForm, OnlineRentalForm, RentalForm, WalkInRentalForm
from ..services.formatting import cancelled_message, modified_message, payment_result_message
from ..use_cases.catalog import browse_catalog
from ..use_cases.payments import online_rentals_of, pay_with_qr
from ..use_cases.renting import create_rental, my_rentals, rentals_visible_to
from ..use_cases.reservation_changes import cancel_rental, modify_rental
from .responses import api_view, read_json, success, valid_form
from .serializers import debt_data, equipment_data, money, rental_data


@api_view("GET")
def catalog(request):
    """Devuelve una página del catálogo con los filtros de la dirección (CU-03)."""
    form = CatalogFilterForm(request.GET)
    valid_form(form)
    page = browse_catalog(request.user, form.filters(), request.GET.get("page"), timezone.now())
    return success(
        {
            "count": page.paginator.count,
            "page": page.number,
            "pages": page.paginator.num_pages,
            "results": [equipment_data(equipment) for equipment in page.object_list],
        }
    )


@api_view("POST")
def create_online_rental(request):
    """Reserva un equipo para el cliente con sesión; queda con el pago pendiente hasta el QR (CU-04)."""
    data = valid_form(OnlineRentalForm(read_json(request)))
    rental = create_rental(request.user, data["equipment"], data["start_datetime"], data["end_datetime"])
    return success(rental_data(rental), "Reserva hecha. Paga con el QR para confirmarla.", status=201)


@api_view("POST")
def pay_rental(request, rental_id):
    """Guarda el resultado del QR simulado de una reserva en línea del cliente (CU-04)."""
    rental = get_object_or_404(online_rentals_of(request.user), pk=rental_id)
    approved = read_json(request).get("approved") is True
    paid = pay_with_qr(rental, approved)
    return success(rental_data(paid), payment_result_message(approved))


@api_view("GET")
def client_rentals(request):
    """Devuelve las rentas del cliente, sus deudas sin pagar y cuánto debe (CU-16)."""
    summary = my_rentals(request.user)
    return success(
        {
            "rentals": [rental_data(rental) for rental in summary.rentals],
            "debts": [debt_data(debt) for debt in summary.debts],
            "debt_total": money(summary.debt_total),
        },
        summary.debt_message if summary.debt_total else "",
    )


@api_view("POST")
def modify_reservation(request, rental_id):
    """Cambia las fechas de una reserva que el usuario puede abrir, con los mismos días (CU-06)."""
    rental = get_object_or_404(rentals_visible_to(request.user), pk=rental_id)
    data = valid_form(RentalForm(read_json(request)))
    modified = modify_rental(rental, data["start_datetime"], data["end_datetime"], request.user)
    return success(rental_data(modified), modified_message(modified))


@api_view("POST")
def cancel_reservation(request, rental_id):
    """Cancela una reserva que el usuario puede abrir (CU-07)."""
    rental = get_object_or_404(rentals_visible_to(request.user), pk=rental_id)
    cancelled = cancel_rental(rental, request.user)
    return success(rental_data(cancelled), cancelled_message(cancelled))


@api_view("POST", roles=[OPERATOR])
def walk_in_rental(request):
    """Registra una renta en tienda para un cliente, pagada en efectivo (CU-05)."""
    data = valid_form(WalkInRentalForm(read_json(request)))
    rental = create_rental(
        data["client"],
        data["equipment"],
        data["start_datetime"],
        data["end_datetime"],
        registered_by=request.user,
    )
    return success(
        rental_data(rental),
        f"Renta registrada: {rental.equipment.inventory_id} para {rental.client.username}.",
        status=201,
    )
