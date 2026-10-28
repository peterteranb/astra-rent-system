"""API del administrador para CU-12 y CU-15: registrar un equipo nuevo y el panel del responsable."""
from django.utils import timezone

from accounts.roles import ADMINISTRATOR

from ..forms import EquipmentForm
from ..services.formatting import equipment_registered_message
from ..use_cases.dashboard import manager_summary
from ..use_cases.inventory import register_equipment
from .responses import api_view, read_json, success, valid_form
from .serializers import client_total_data, equipment_data, money, rental_data


@api_view("POST", roles=[ADMINISTRATOR])
def register_equipment_view(request):
    """Registra un equipo nuevo «Disponible» (CU-12)."""
    data = valid_form(EquipmentForm(read_json(request)))
    equipment = register_equipment(**data, registered_by=request.user)
    return success(equipment_data(equipment), equipment_registered_message(equipment), status=201)


@api_view("GET", roles=[ADMINISTRATOR])
def manager_dashboard(request):
    """Devuelve las seis listas del panel y la deuda total del sistema (CU-15)."""
    summary = manager_summary(timezone.now())
    return success(
        {
            "active": dashboard_list(summary.active, rental_data),
            "overdue": dashboard_list(summary.overdue, rental_data),
            "today": dashboard_list(summary.today, rental_data),
            "pending_payment": dashboard_list(summary.pending_payment, rental_data),
            "to_review": dashboard_list(summary.to_review, equipment_data),
            "debts_by_client": dashboard_list(summary.debts_by_client, client_total_data),
            "debt_total": money(summary.debt_total),
        }
    )


def dashboard_list(listing, to_data):
    """Una lista del panel en JSON: cuántas hay en total y sus primeras filas."""
    return {"total": listing.total, "rows": [to_data(row) for row in listing.rows]}
