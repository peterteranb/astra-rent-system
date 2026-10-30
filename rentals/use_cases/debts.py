"""Deudas (CU-11): crearlas al devolver con atraso (CU-09) o al revisar con daño (CU-10), sumarlas, listarlas y cobrarlas.

«Mis rentas» (CU-16) y el panel (CU-15) leen las deudas desde aquí.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone

from ..errors import DebtStateError
from ..models import Debt
from ..services.events import debt_context, log_event, logs_rejection
from ..services.formatting import local_text
from ..services.notifications import send_debt_created


@dataclass(frozen=True)
class DebtsOverview:
    """Lo que ve el operador en «Deudas»: cada deuda sin pagar y el total de cada cliente (CU-11)."""

    debts: list[Debt]
    totals: list[dict]


def charge_debt(rental, reason, amount, charged_by):
    """Crea la deuda de la renta por ese motivo, avisa al cliente y la devuelve; None si ya existía (ENT-76).

    charged_by es quien registró la devolución o la revisión que la generó.
    """
    debt, created = Debt.objects.get_or_create(
        rental=rental, reason=reason, defaults={"amount": amount}
    )
    if not created:
        return None
    log_event("DEBT_CREATED", **debt_context(debt, charged_by.username))
    send_debt_created(debt)
    return debt


def pending_debts():
    """Devuelve todas las deudas sin pagar con su cliente y su equipo, la más nueva primero (ENT-100)."""
    return (
        Debt.objects.pending()
        .select_related("rental__client", "rental__equipment")
        .order_by("-created_at")
    )


def debts_overview() -> DebtsOverview:
    """Devuelve las deudas sin pagar, una por una, y el total que debe cada cliente (CU-11)."""
    return DebtsOverview(list(pending_debts()), list(pending_totals_by_client()))


def pending_debts_of(client):
    """Devuelve las deudas sin pagar del cliente, la más nueva primero (CU-16)."""
    return pending_debts().filter(rental__client=client)


def debt_total_of(client) -> Decimal:
    """Suma las deudas sin pagar del cliente; se calcula, no se guarda (ENT-76)."""
    return Debt.objects.pending().filter(rental__client=client).total()


def pending_totals_by_client():
    """Devuelve el usuario, el nombre y la deuda total de cada cliente que debe, el de la deuda más nueva primero (ENT-100)."""
    return (
        Debt.objects.pending()
        .values("rental__client__username", "rental__client__first_name", "rental__client__last_name")
        .annotate(total=Sum("amount"), latest=Max("created_at"))
        .order_by("-latest")
    )


def attempted_debt_payment(debt, staff_user):
    """La deuda que se quiso cobrar, para el log del rechazo."""
    return debt_context(debt, staff_user.username)


@logs_rejection("DEBT_PAYMENT_REJECTED", attempted_debt_payment)
def pay_debt(debt, staff_user) -> Debt:
    """Guarda que el cliente pagó esta deuda en la tienda y qué operador la cobró (ENT-76).

    Lanza DebtStateError si ya estaba pagada; entonces nada cambia.
    """
    with transaction.atomic():
        # Bloquea la fila: dos operadores no cobran la misma deuda dos veces.
        locked_debt = Debt.objects.select_for_update().get(pk=debt.pk)
        check_debt_is_pending(locked_debt)
        locked_debt.paid_at = timezone.now()
        locked_debt.paid_received_by = staff_user
        locked_debt.save(update_fields=["paid_at", "paid_received_by"])
    log_event("DEBT_PAID", **debt_context(locked_debt, staff_user.username))
    return locked_debt


def check_debt_is_pending(debt):
    """Lanza DebtStateError si la deuda ya se pagó."""
    if debt.is_paid:
        raise DebtStateError(f"Esta deuda ya se pagó el {local_text(debt.paid_at)}.")
