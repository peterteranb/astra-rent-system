"""Páginas del operador para CU-11: las deudas pendientes y el registro de su pago.

Leen la petición, llaman a use_cases/debts.py y eligen la plantilla; las reglas están ahí.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.roles import OPERATOR, role_required

from ..errors import OperationRejectedError
from ..models import Debt
from ..services.formatting import debt_paid_message
from ..use_cases.debts import debts_overview, pay_debt


@role_required(OPERATOR)
def staff_debts(request):
    """Muestra las deudas pendientes, una por una, y el total que debe cada cliente."""
    return render(request, "rentals/staff_debts.html", {"overview": debts_overview()})


# role_required va afuera: un visitante va al login antes de que require_POST responda 405.
@role_required(OPERATOR)
@require_POST
def pay_debt_view(request, debt_id):
    """Registra que el cliente pagó una deuda en la tienda y vuelve a la lista (CU-11)."""
    debt = get_object_or_404(Debt.objects.select_related("rental__client"), pk=debt_id)
    try:
        pay_debt(debt, request.user)
    except OperationRejectedError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, debt_paid_message(debt))
    # Redirige después del POST: recargar la página no lo envía otra vez.
    return redirect("staff_debts")
