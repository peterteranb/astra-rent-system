"""URLs de la API JSON bajo /api/: sesión, cliente, operador, mantenimiento y administrador."""
from django.urls import path, re_path

from accounts import api as accounts_api

from . import debts, handover, inventory, renting, review
from .responses import not_found

urlpatterns = [
    path("csrf/", accounts_api.csrf),
    path("auth/login/", accounts_api.login_view),
    path("auth/logout/", accounts_api.logout_view),
    path("auth/me/", accounts_api.me),
    path("auth/signup/", accounts_api.sign_up),
    path("auth/profile/", accounts_api.update_my_profile),
    path("auth/password/", accounts_api.change_password),
    path("auth/password-reset/", accounts_api.request_password_reset),
    path("catalog/", renting.catalog),
    path("rentals/", renting.create_online_rental),
    path("rentals/<int:rental_id>/pay/", renting.pay_rental),
    path("rentals/<int:rental_id>/modify/", renting.modify_reservation),
    path("rentals/<int:rental_id>/cancel/", renting.cancel_reservation),
    path("my-rentals/", renting.client_rentals),
    path("staff/clients/", accounts_api.store_clients),
    path("staff/rentals/", renting.walk_in_rental),
    path("staff/reservations/", handover.staff_reservations),
    path("staff/rentals/<int:rental_id>/pickup/", handover.pickup_reservation),
    path("staff/returns/", handover.staff_returns),
    path("staff/rentals/<int:rental_id>/return/", handover.return_rental),
    path("staff/debts/", debts.staff_debts),
    path("staff/debts/<int:debt_id>/pay/", debts.pay_debt_view),
    path("maintenance/equipment/", review.maintenance_equipment),
    path("maintenance/equipment/<str:inventory_id>/review/", review.review_equipment_view),
    path("admin/equipment/", inventory.register_equipment_view),
    path("manager/dashboard/", inventory.manager_dashboard),
    # Cualquier otra dirección bajo /api/ responde 404 en JSON y no con la página HTML.
    re_path(r"^", not_found),
]
