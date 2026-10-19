"""Páginas de CU-01, CU-02 y CU-06: catálogo, renta en línea y en tienda, confirmación, cancelación y «Mis rentas».

Leen la petición, llaman a renting.py y eligen la plantilla; las reglas están en renting.py y rules.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .. import rules
from ..errors import EquipmentNotAvailableError, OperationRejectedError
from ..forms import RentalForm, WalkInRentalForm
from ..models import Equipment, Rental
from ..renting import (
    cancel_rental,
    catalog_entries,
    create_rental,
    find_clients,
    rentals_of,
    visible_rental,
)
from ..roles import OPERATOR, role_required


@login_required
def catalog(request):
    """Muestra los equipos que el cliente puede elegir, cada uno con sus próximos periodos ocupados."""
    return render(
        request, "rentals/catalog.html", {"catalog_entries": catalog_entries(timezone.now())}
    )


@login_required
def rent_equipment(request, inventory_id):
    """Muestra el formulario de un equipo e intenta rentarlo (CU-01)."""
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)
    form = RentalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            rental = create_rental(
                request.user,
                equipment,
                form.cleaned_data["start_datetime"],
                form.cleaned_data["end_datetime"],
            )
        except EquipmentNotAvailableError as error:
            # Fechas ocupadas: vuelve al catálogo, donde ve cuándo está libre.
            messages.error(request, str(error))
            return redirect("catalog")
        except OperationRejectedError as error:
            # Fechas u horas inválidas: se queda en el formulario para corregirlas.
            form.add_error(None, str(error))
        else:
            return redirect("rental_confirmation", rental_id=rental.pk)
    return render(request, "rentals/rent_form.html", rental_form_context(equipment, form))


@login_required
def rental_confirmation(request, rental_id):
    """Muestra la renta confirmada a su cliente o al operador que la registró."""
    return render(
        request,
        "rentals/rental_confirmation.html",
        {
            "rental": visible_rental(request.user, rental_id),
            "earliest_pickup_time": rules.EARLIEST_PICKUP_TIME,
        },
    )


def rental_form_context(equipment, form):
    """Datos que necesita la plantilla del formulario de renta, con los límites de las reglas."""
    return {
        "equipment": equipment,
        "form": form,
        "earliest_pickup_time": rules.EARLIEST_PICKUP_TIME,
        "latest_return_time": rules.LATEST_RETURN_TIME,
        "max_days": rules.MAX_RENTAL_DURATION.days,
    }


# role_required va afuera: un visitante va al login antes de que require_POST responda 405.
@role_required(OPERATOR)
@require_POST
def cancel_reservation(request, rental_id):
    """Cancela una reserva y vuelve a la lista de reservas (CU-06)."""
    rental = get_object_or_404(Rental, pk=rental_id)
    try:
        cancel_rental(rental, request.user)
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            f"Reserva cancelada: {rental.equipment.inventory_id} de {rental.client.username}.",
        )
    # Redirige después del POST: recargar la página no lo envía otra vez.
    return redirect("staff_reservations")


@role_required(OPERATOR)
def walk_in_rental(request):
    """Busca un cliente por GET y registra una renta en tienda para él por POST (CU-02)."""
    # El formulario se envía a la misma dirección con ?q=, así los resultados
    # de la búsqueda siguen en la página si la renta se rechaza.
    query = request.GET.get("q", "")
    form = WalkInRentalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            rental = create_rental(
                form.cleaned_data["client"],
                form.cleaned_data["equipment"],
                form.cleaned_data["start_datetime"],
                form.cleaned_data["end_datetime"],
                registered_by=request.user,
                picked_up_now=form.cleaned_data["takes_it_now"],
            )
        except OperationRejectedError as error:
            form.add_error(None, str(error))
        else:
            return redirect("rental_confirmation", rental_id=rental.pk)
    return render(
        request,
        "rentals/walk_in_rental.html",
        {"form": form, "query": query, "clients": find_clients(query)},
    )


@login_required
def client_rentals(request):
    """Muestra las rentas del cliente con su estado (HU-08)."""
    return render(request, "rentals/client_rentals.html", {"rentals": rentals_of(request.user)})
