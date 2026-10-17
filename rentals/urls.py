"""Client pages of PRE-CU-01 (catalog, rental form, confirmation) and the staff pages."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("home/", views.home, name="home"),
    path("equipment/<str:inventory_id>/rent/", views.rent_equipment, name="rent_equipment"),
    path("rentals/<int:rental_id>/", views.rental_confirmation, name="rental_confirmation"),
    path("staff/reservations/", views.staff_reservations, name="staff_reservations"),
    path("staff/returns/", views.staff_returns, name="staff_returns"),
    path("maintenance/", views.maintenance, name="maintenance"),
]
