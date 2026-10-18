"""Client pages of PRE-CU-01 (catalog, rental form, confirmation) and the staff pages."""
from django.urls import path

from .views import handover, home, renting, review

urlpatterns = [
    path("", renting.catalog, name="catalog"),
    path("home/", home.home, name="home"),
    path("equipment/<str:inventory_id>/rent/", renting.rent_equipment, name="rent_equipment"),
    path("rentals/<int:rental_id>/", renting.rental_confirmation, name="rental_confirmation"),
    path("staff/reservations/", handover.staff_reservations, name="staff_reservations"),
    path(
        "staff/reservations/<int:rental_id>/pickup/",
        handover.pickup_reservation,
        name="register_pickup",
    ),
    path("staff/returns/", handover.staff_returns, name="staff_returns"),
    path("maintenance/", review.maintenance, name="maintenance"),
]
