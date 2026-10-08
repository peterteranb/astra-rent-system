"""Views of PRE-CU-01. They read the request, call the service and
choose a template; the business rules live in services.py and rules.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from . import rules
from .errors import EquipmentNotAvailableError, RentalRejectedError
from .forms import RentalForm
from .models import Equipment, Rental
from .services import create_rental, list_catalog


@login_required
def catalog(request):
    """Step 4: show the units the client can choose."""
    return render(request, "rentals/catalog.html", {"equipment_list": list_catalog()})


@login_required
def rent_equipment(request, inventory_id):
    """Steps 5 to 8: show the form for one unit and try to rent it."""
    # A unit that is not in the inventory answers 404 (PRE-CU-01
    # precondition "the unit exists").
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
            return redirect("rental_confirmation", rental_id=rental.pk)
        except EquipmentNotAvailableError as error:
            # E1: show the cause and send the client back to the catalog.
            messages.error(request, str(error))
            return redirect("catalog")
        except RentalRejectedError as error:
            # Wrong dates or hours: stay on the form so the client can fix them.
            form.add_error(None, str(error))

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
