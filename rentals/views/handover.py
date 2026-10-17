"""Operator pages to hand over reserved units and receive them back."""
from django.shortcuts import render

from ..roles import OPERATOR, role_required


@role_required(OPERATOR)
def staff_reservations(request):
    """Operator page to hand over reservations (under construction)."""
    return render(request, "rentals/under_construction.html", {"page_title": "Reservas por entregar"})


@role_required(OPERATOR)
def staff_returns(request):
    """Operator page to register returns (under construction)."""
    return render(request, "rentals/under_construction.html", {"page_title": "Devoluciones"})
