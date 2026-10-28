"""Caso de uso CU-15: el panel del responsable junta en una página lo que necesita atención (ENT-87, PRE-06, PRE-08)."""
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum

from .models import Debt, Rental
from .payments import pending_totals_by_client
from .review import equipment_to_review

# Cada lista del panel muestra las primeras; el enlace al admin muestra todas.
ROWS_PER_LIST = 10


@dataclass(frozen=True)
class DashboardList:
    """Una lista del panel: cuántas hay en total y las primeras filas."""

    total: int
    rows: list


@dataclass(frozen=True)
class ManagerSummary:
    """Las seis listas del panel y la deuda total del sistema."""

    active: DashboardList
    overdue: DashboardList
    today: DashboardList
    pending_payment: DashboardList
    to_review: DashboardList
    debts_by_client: DashboardList
    debt_total: Decimal


def manager_summary(now) -> ManagerSummary:
    """Devuelve lo que ve el responsable en el momento now; cada lista es una consulta y su conteo."""
    rentals = Rental.objects.select_related("equipment", "client").order_by("end_datetime")
    return ManagerSummary(
        active=dashboard_list(rentals.active_at(now)),
        overdue=dashboard_list(rentals.overdue_at(now)),
        today=dashboard_list(rentals.reserved_for_today_at(now).order_by("start_datetime")),
        pending_payment=dashboard_list(rentals.pending_payment_at(now).order_by("start_datetime")),
        to_review=dashboard_list(equipment_to_review()),
        debts_by_client=dashboard_list(pending_totals_by_client()),
        debt_total=Debt.objects.pending().aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
    )


def dashboard_list(queryset) -> DashboardList:
    """Arma una lista del panel con su total y sus primeras ROWS_PER_LIST filas."""
    return DashboardList(queryset.count(), list(queryset[:ROWS_PER_LIST]))
