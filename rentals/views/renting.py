"""Páginas de CU-03 a CU-07 y CU-16: catálogo, renta en línea con QR y en tienda, confirmación, modificar, cancelar y «Mis rentas».

Leen la petición, llaman a renting.py y eligen la plantilla; las reglas están en renting.py y rules.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .. import rules
from ..errors import EquipmentNotAvailableError, OperationRejectedError
from ..formatting import local_text
from ..forms import CatalogFilterForm, RentalForm, WalkInRentalForm
from ..models import Equipment, Rental
from ..payments import debt_total_of, pay_with_qr, pending_debts_of
from ..renting import (
    cancel_rental,
    catalog_page,
    create_rental,
    find_clients,
    modify_rental,
    rentals_of,
    search_catalog,
    visible_rental,
)
from ..roles import MAINTENANCE, OPERATOR, has_role, role_required


@login_required
def catalog(request):
    """Muestra el catálogo filtrado, de 20 en 20, con los próximos periodos ocupados de cada equipo (CU-03)."""
    now = timezone.now()
    staff = has_role(request.user, OPERATOR) or has_role(request.user, MAINTENANCE)
    form = CatalogFilterForm(request.GET or None)
    equipment = search_catalog(form.filters(), now, staff=staff)
    return render(
        request,
        "rentals/catalog.html",
        {"form": form, "page": catalog_page(equipment, request.GET.get("page"), now), "staff": staff},
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
            return redirect("pay_rental", rental_id=rental.pk)
    return render(request, "rentals/rent_form.html", rental_form_context(equipment, form))


@login_required
def pay_rental(request, rental_id):
    """Muestra el QR simulado de una reserva en línea y guarda el botón que presiona el cliente (CU-04)."""
    rental = get_object_or_404(Rental, pk=rental_id, client=request.user, registered_by__isnull=True)
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
    if approved:
        messages.success(request, "Pago recibido. Tu renta está confirmada.")
        return
    messages.warning(
        request,
        "Tu reserva está hecha, pero el pago no se completó. Paga en la tienda al recoger el equipo.",
    )


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
        "equipment_daily_price": rules.daily_price_for(equipment.value),
        "form": form,
        "earliest_pickup_time": rules.EARLIEST_PICKUP_TIME,
        "latest_return_time": rules.LATEST_RETURN_TIME,
        "max_days": rules.MAX_RENTAL_DAYS,
    }


@login_required
def modify_reservation(request, rental_id):
    """Muestra las fechas de una reserva y guarda las nuevas, con los mismos días (CU-06)."""
    rental = visible_rental(request.user, rental_id)
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
            messages.success(
                request,
                f"Reserva modificada: {modified.equipment.inventory_id} ahora va del "
                f"{local_text(modified.start_datetime)} al {local_text(modified.end_datetime)}.",
            )
            return redirect(reservations_page_for(request.user))
    return render(
        request,
        "rentals/modify_form.html",
        {**rental_form_context(rental.equipment, form), "rental": rental},
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
    rental = visible_rental(request.user, rental_id)
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
    return redirect(reservations_page_for(request.user))


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
    """Muestra las rentas del cliente con su estado y su pago, y lo que debe (CU-16)."""
    return render(
        request,
        "rentals/client_rentals.html",
        {
            "rentals": rentals_of(request.user),
            "debts": pending_debts_of(request.user),
            "debt_total": debt_total_of(request.user),
        },
    )
