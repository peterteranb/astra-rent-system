"""Páginas de CU-03 a CU-07 y CU-16: catálogo, renta en línea con QR y en tienda, confirmación, modificar, cancelar y «Mis rentas».

Leen la petición, llaman a use_cases/ (catalog, renting, payments y reservation_changes) y eligen la plantilla; las reglas están ahí y en rules.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.roles import OPERATOR, has_role, role_required

from .. import rules
from ..errors import EquipmentNotAvailableError, OperationRejectedError
from ..forms import CatalogFilterForm, RentalForm, WalkInRentalForm
from ..models import Equipment
from ..services.formatting import cancelled_message, modified_message, payment_result_message
from ..use_cases.catalog import browse_catalog
from ..use_cases.payments import online_rentals_of, pay_with_qr
from ..use_cases.renting import create_rental, find_clients, my_rentals, rentals_visible_to
from ..use_cases.reservation_changes import cancel_rental, modify_rental


@login_required
def catalog(request):
    """Muestra el catálogo filtrado, de 20 en 20, sin etiquetas de libre u ocupado (CU-03, ENT-99)."""
    form = CatalogFilterForm(request.GET or None)
    page = browse_catalog(request.user, form.filters(), request.GET.get("page"), timezone.now())
    return render(request, "rentals/catalog.html", {"form": form, "page": page, **period_limits()})


@login_required
def rent_equipment(request, inventory_id):
    """Muestra el formulario de un equipo e intenta rentarlo (CU-04)."""
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
            # Fechas ocupadas: vuelve al catálogo con el mensaje, que dice cuándo está libre.
            messages.error(request, str(error))
            return redirect("catalog")
        except OperationRejectedError as error:
            # Fechas u horas inválidas: se queda en el formulario para corregirlas.
            form.add_error(None, str(error))
        else:
            return redirect("pay_rental", rental_id=rental.pk)
    return render(
        request, "rentals/rent_form.html", {"equipment": equipment, "form": form, **period_limits()}
    )


@login_required
def pay_rental(request, rental_id):
    """Muestra el QR simulado de una reserva en línea y guarda el botón que presiona el cliente (CU-04)."""
    rental = get_object_or_404(online_rentals_of(request.user), pk=rental_id)
    if request.method != "POST":
        return render(request, "rentals/pay_rental.html", {"rental": rental})
    approved = request.POST.get("result") == "approved"
    try:
        pay_with_qr(rental, approved)
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        show_payment_result(request, approved)
    return redirect("rental_confirmation", rental_id=rental.pk)


def show_payment_result(request, approved):
    """Muestra al cliente si el pago QR se completó o si paga al recoger (ENT-67)."""
    level = messages.SUCCESS if approved else messages.WARNING
    messages.add_message(request, level, payment_result_message(approved))


@login_required
def rental_confirmation(request, rental_id):
    """Muestra la renta confirmada a su cliente o al operador que la registró."""
    return render(
        request,
        "rentals/rental_confirmation.html",
        {"rental": visible_rental(request, rental_id), **period_limits()},
    )


def visible_rental(request, rental_id):
    """Devuelve la renta si el usuario puede abrirla; si no, responde 404 sin decir que existe."""
    return get_object_or_404(rentals_visible_to(request.user), pk=rental_id)


def period_limits():
    """Los horarios y la duración máxima que muestran las páginas con fechas (ENT-19, ENT-72)."""
    return {
        "earliest_pickup_time": rules.EARLIEST_PICKUP_TIME,
        "latest_return_time": rules.LATEST_RETURN_TIME,
        "max_days": rules.MAX_RENTAL_DAYS,
    }


@login_required
def modify_reservation(request, rental_id):
    """Muestra las fechas de una reserva y guarda las nuevas, con los mismos días (CU-06)."""
    rental = visible_rental(request, rental_id)
    form = RentalForm(request.POST or None, initial=current_period(rental))
    if request.method == "POST" and form.is_valid():
        try:
            modified = modify_rental(
                rental,
                form.cleaned_data["start_datetime"],
                form.cleaned_data["end_datetime"],
                request.user,
            )
        except OperationRejectedError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, modified_message(modified))
            return redirect(reservations_page_for(request.user))
    return render(
        request,
        "rentals/modify_form.html",
        {
            "equipment": rental.equipment,
            "form": form,
            "rental": rental,
            "back_page": reservations_page_for(request.user),
            **period_limits(),
        },
    )


def current_period(rental):
    """Fechas y horas actuales de la reserva, para llenar el formulario de modificar."""
    start = timezone.localtime(rental.start_datetime)
    end = timezone.localtime(rental.end_datetime)
    return {
        "start_date": start.date(),
        "start_time": start.time(),
        "end_date": end.date(),
        "end_time": end.time(),
    }


def reservations_page_for(user):
    """Página a la que vuelve quien cambió una reserva: el personal a sus reservas, el cliente a las suyas."""
    return "staff_reservations" if has_role(user, OPERATOR) else "client_rentals"


@login_required
@require_POST
def cancel_reservation(request, rental_id):
    """Cancela una reserva del cliente o, para el personal, de cualquiera, y vuelve a su lista (CU-07)."""
    rental = visible_rental(request, rental_id)
    try:
        cancel_rental(rental, request.user)
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, cancelled_message(rental))
    # Redirige después del POST: recargar la página no lo envía otra vez.
    return redirect(reservations_page_for(request.user))


@role_required(OPERATOR)
def walk_in_rental(request):
    """Busca un cliente por GET y registra una renta en tienda para él por POST (CU-05)."""
    # Se envía a la misma dirección con ?q=: si la renta se rechaza, los resultados de la búsqueda siguen ahí.
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
    """Muestra las rentas del cliente con su estado y su pago, y lo que debe (CU-16)."""
    return render(request, "rentals/client_rentals.html", {"summary": my_rentals(request.user)})
