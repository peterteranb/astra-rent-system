"""Client pages of PRE-CU-01: catalog, rental form and confirmation."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("equipment/<str:inventory_id>/rent/", views.rent_equipment, name="rent_equipment"),
    path("rentals/<int:rental_id>/", views.rental_confirmation, name="rental_confirmation"),
]
