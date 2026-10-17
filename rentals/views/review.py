"""Maintenance page to review returned units."""
from django.shortcuts import render

from ..roles import MAINTENANCE, role_required


@role_required(MAINTENANCE)
def maintenance(request):
    """Maintenance page to review returned units (under construction)."""
    return render(request, "rentals/under_construction.html", {"page_title": "Mantenimiento"})
