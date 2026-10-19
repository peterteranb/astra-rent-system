"""Views of PRE-CU-01 (renting). They read the request, call the use case
and choose a template; the business rules live in renting.py and rules.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model #necesario para walk-in rentals
from django.utils.dateparse import parse_datetime #necesario para walk-in rentals
from django.utils import timezone #necesario para mostrar las fechas ocupadas de cada equipo en el catalogo

from .. import rules
from ..errors import EquipmentNotAvailableError, OperationRejectedError
from ..forms import RentalForm
from ..models import Equipment, Rental
from ..renting import catalog_entries, create_rental
from ..models import Rental
from ..renting import cancel_rental
from ..roles import OPERATOR, role_required

User = get_user_model() #necesario para walk-in rentals


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
    """Step 9: show the confirmed rental to the client who made it."""
    # Filtering by client means nobody can open another client's rental.
    rental = get_object_or_404(Rental, pk=rental_id, client=request.user)
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

@require_POST
@role_required(OPERATOR)
def cancel_reservation(request, rental_id):
    """Permite al operador cancelar una reserva que aún no ha sido recogida."""
    rental = get_object_or_404(Rental, pk=rental_id)

    try:
        cancel_rental(rental, request.user)
        messages.success(
            request,
            f"La reserva del equipo {rental.equipment.inventory_id} fue cancelada correctamente.",
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("staff_reservations")

@role_required(OPERATOR)
def walk_in_rental(request):
    """Permite al operador registrar una renta en tienda buscando al cliente por ID/username."""
    client_found = None
    client_query = request.GET.get("client_id", "").strip()

    # Si se realizó una búsqueda de cliente
    if client_query:
        client_found = User.objects.filter(username=client_query).first() or \
                       User.objects.filter(id=client_query if client_query.isdigit() else None).first()
        if not client_found:
            messages.error(request, f"No se encontró ningún cliente con el ID/usuario '{client_query}'.")

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        inventory_id = request.POST.get("inventory_id")
        start_raw = request.POST.get("start_datetime")
        end_raw = request.POST.get("end_datetime")

        client = get_object_or_404(User, pk=client_id)
        equipment = get_object_or_404(Equipment, inventory_id=inventory_id)

        try:
            start_dt = parse_datetime(start_raw)
            end_dt = parse_datetime(end_raw)

            rental = create_rental(
                client=client,
                equipment=equipment,
                start_datetime=start_dt,
                end_datetime=end_dt,
                registered_by=request.user, # Operador que atiende
            )
            messages.success(
                request,
                f"Renta registrada exitosamente para {client.get_full_name() or client.username}.",
            )
            return redirect("staff_reservations")
        except Exception as e:
            messages.error(request, str(e))

    equipments = Equipment.objects.filter(status="available")
    return render(
        request,
        "rentals/walk_in_rental.html",
        {
            "client_found": client_found,
            "client_query": client_query,
            "equipments": equipments,
        },
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
