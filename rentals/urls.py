"""URLs de las páginas del cliente (catálogo, renta, confirmación, «Mis rentas») y del personal."""
from django.urls import path

from .views import dashboard, debts, handover, home, inventory, renting, review

urlpatterns = [
    path("", renting.catalog, name="catalog"),
    path("home/", home.home, name="home"),
    path("equipment/new/", inventory.register_equipment_view, name="register_equipment"),
    path("manager/", dashboard.manager_dashboard, name="manager_dashboard"),
    path("equipment/<str:inventory_id>/rent/", renting.rent_equipment, name="rent_equipment"),
    path("rentals/<int:rental_id>/", renting.rental_confirmation, name="rental_confirmation"),
    path("rentals/<int:rental_id>/pay/", renting.pay_rental, name="pay_rental"),
    path("rentals/<int:rental_id>/modify/", renting.modify_reservation, name="modify_reservation"),
    path("rentals/<int:rental_id>/cancel/", renting.cancel_reservation, name="cancel_reservation"),
    path("staff/reservations/", handover.staff_reservations, name="staff_reservations"),
    path(
        "staff/reservations/<int:rental_id>/pickup/",
        handover.pickup_reservation,
        name="register_pickup",
    ),
    path("staff/returns/", handover.staff_returns, name="staff_returns"),
    path("staff/returns/<int:rental_id>/", handover.return_rental, name="return_rental"),
    path("maintenance/", review.maintenance, name="maintenance"),
    path("maintenance/<str:inventory_id>/", review.review_unit, name="review_unit"),
    path("staff/walk-in/", renting.walk_in_rental, name="walk_in_rental"),
    path("my-rentals/", renting.client_rentals, name="client_rentals"),
    path("staff/debts/", debts.staff_debts, name="staff_debts"),
    path("staff/debts/<int:debt_id>/pay/", debts.pay_debt_view, name="pay_debt"),
]
