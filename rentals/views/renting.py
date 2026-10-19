"""Views of PRE-CU-01 (renting). They read the request, call the use case
and choose a template; the business rules live in renting.py and rules.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone #necesario para mostrar las fechas ocupadas de cada equipo en el catalogo

from .. import rules
from ..errors import EquipmentNotAvailableError, OperationRejectedError
from ..forms import RentalForm, WalkInRentalForm
from ..models import Equipment, Rental
from ..renting import catalog_entries, create_rental, find_clients
from ..models import Rental
from ..renting import cancel_rental
from ..roles import OPERATOR, role_required


@login_required
def catalog(request):
    """Step 4: show the units the client can choose, each with its next busy periods."""
    return render(
        request, "rentals/catalog.html", {"catalog_entries": catalog_entries(timezone.now())}
    )


@login_required
def rent_equipment(request, inventory_id):
    """Steps 5 to 8: show the form for one unit and try to rent it."""
    # A unit that is not in the inventory answers 404 (PRE-CU-01
    # precondition "the unit exists").
    equipment = get_object_or_404(Equipment, inventory_id=inventory_id)

    if request.method == "POST":
        form = RentalForm(request.POST)
        if form.is_valid():
            try:
                rental = create_rental(
                    request.user,
                    equipment,
                    form.cleaned_data["start_datetime"],
                    form.cleaned_data["end_datetime"],
                )
                return redirect("rental_confirmation", rental_id=rental.pk)
            except EquipmentNotAvailableError as error:
                # E1: show the cause and send the client back to the catalog.
                messages.error(request, str(error))
                return redirect("catalog")
            except OperationRejectedError as error:
                # Wrong dates or hours: stay on the form so the client can fix them.
                form.add_error(None, str(error))
    else:
        form = RentalForm()

    return render(request, "rentals/rent_form.html", rental_form_context(equipment, form))


@login_required
def rental_confirmation(request, rental_id):
    """Step 9: show the confirmed rental to its client or to the operator who registered it."""
    # Filtering by user means nobody else can open the rental (#50).
    rental = get_object_or_404(
        Rental, Q(client=request.user) | Q(registered_by=request.user), pk=rental_id
    )
    return render(
        request,
        "rentals/rental_confirmation.html",
        {"rental": rental, "earliest_pickup_time": rules.EARLIEST_PICKUP_TIME},
    )


def rental_form_context(equipment, form):
    """Data the rental form template needs, including the rule limits."""
    return {
        "equipment": equipment,
        "form": form,
        "earliest_pickup_time": rules.EARLIEST_PICKUP_TIME,
        "latest_return_time": rules.LATEST_RETURN_TIME,
        "max_days": rules.MAX_RENTAL_DURATION.days,
    }

# role_required goes outside so a visitor is sent to the login before
# require_POST answers 405 to a GET.
@role_required(OPERATOR)
@require_POST
def cancel_reservation(request, rental_id):
    """Cancel one reservation and go back to the list of reservations (#49)."""
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
    # Redirect after the POST so reloading the page does not send it again.
    return redirect("staff_reservations")

@role_required(OPERATOR)
def walk_in_rental(request):
    """Find a client by GET and register a store rental for them by POST (PRE-CU-02)."""
    # The form posts to the same address with ?q=, so the search results
    # stay on the page when the rental is rejected.
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
            # Same rejections as online; stay on the form so the operator can fix it.
            form.add_error(None, str(error))
        else:
            return redirect("rental_confirmation", rental_id=rental.pk)
    return render(
        request,
        "rentals/walk_in_rental.html",
        {"form": form, "query": query, "clients": find_clients(query)},
    )


@login_required
def client_rentals_view(request):
    """Muestra al cliente la lista de sus rentas (activas e historial)."""
    # Obtenemos las rentas del usuario logueado, ordenadas por fecha de inicio
    rentals = request.user.rentals.all().order_by("-start_datetime")

    return render(
        request,
        "rentals/client_rentals.html",
        {"rentals": rentals}
    )
